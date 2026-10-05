"""Deterministic text-package maintenance, using only Python's standard library."""
import hashlib
import json
import os
import re
import stat
from contextlib import contextmanager
from dataclasses import dataclass, field

MANIFEST = 'workharbor.json'
MAX_MANIFEST = 256 << 10
MAX_FILES = 1024
MAX_FILE = 1 << 20
MAX_TOTAL = 16 << 20
MAX_ENTRIES = 16384
MAX_INVENTORY = MAX_FILES * (64 + 2 + 240 + 1)
IDENTIFIER = re.compile(r'[a-z][a-z0-9_-]{0,63}\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')
COMMIT = re.compile(r'[0-9a-f]{40}\Z')


class PackageError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise PackageError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def valid_path(name):
    return (isinstance(name, str) and 0 < len(name) <= 240
            and re.fullmatch(r'[A-Za-z0-9._/-]+', name) is not None
            and all(part not in ('', '.', '..') and part.lower() != '.git'
                    and not part.endswith('.') for part in name.split('/')))


def text(data):
    try:
        value = data.decode('utf-8')
    except UnicodeDecodeError:
        return False
    return all(ord(c) >= 32 or c in '\n\r\t' for c in value)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON field: ' + key)
        result[key] = value
    return result


def decode(data):
    require(text(data), 'invalid UTF-8 JSON')
    try:
        def invalid_constant(value):
            raise PackageError('invalid JSON constant: ' + value)
        value = json.loads(data.decode('utf-8'), object_pairs_hook=unique_object,
                           parse_constant=invalid_constant)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise PackageError('invalid UTF-8 JSON: ' + str(error)) from error
    def valid_unicode(node):
        if isinstance(node, str):
            require(not any(0xD800 <= ord(c) <= 0xDFFF for c in node), 'invalid Unicode surrogate in JSON')
        elif isinstance(node, dict):
            for key, item in node.items():
                valid_unicode(key)
                valid_unicode(item)
        elif isinstance(node, list):
            for item in node:
                valid_unicode(item)
    valid_unicode(value)
    return value


def object_fields(value, required, optional=()):
    require(isinstance(value, dict), 'JSON object required')
    require(set(required) <= set(value) <= set(required) | set(optional),
            'missing or unknown JSON fields')
    return value


def strings(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def integer(value):
    return type(value) is int


def identity(info):
    return info.st_dev, info.st_ino


def stable(info):
    return (identity(info), info.st_mode, info.st_uid, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def safe_directory(info):
    return (stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and info.st_mode & 0o7022 == 0)


def canonical_root(root):
    require(os.path.isabs(root) and os.path.normpath(root) == root
            and os.path.realpath(root) == root,
            'source root must be canonical without symlinks')


@contextmanager
def directory_fd(path, parent=None):
    before = os.stat(path, dir_fd=parent, follow_symlinks=False)
    require(safe_directory(before), 'unsafe directory ownership or permissions: ' + path)
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_DIRECTORY,
                 dir_fd=parent)
    try:
        require(stable(before) == stable(os.fstat(fd)), 'directory changed during open: ' + path)
        yield fd
        current = os.stat(path, dir_fd=parent, follow_symlinks=False)
        require(identity(current) == identity(before) and safe_directory(current),
                'directory identity changed: ' + path)
    finally:
        os.close(fd)


def read_at(parent, name, limit):
    before = os.stat(name, dir_fd=parent, follow_symlinks=False)
    require(stat.S_ISREG(before.st_mode), name + ': not a regular file')
    fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=parent)
    try:
        opened = os.fstat(fd)
        require(stable(before) == stable(opened) and stat.S_ISREG(opened.st_mode)
                and opened.st_uid == os.getuid() and opened.st_nlink == 1
                and opened.st_mode & 0o7133 == 0,
                name + ': unsafe file identity, ownership or permissions')
        require(opened.st_size <= limit, name + ': size limit exceeded')
        chunks, count = [], 0
        while count <= limit:
            chunk = os.read(fd, min(65536, limit + 1 - count))
            if not chunk:
                break
            chunks.append(chunk)
            count += len(chunk)
        data = b''.join(chunks)
        current = os.stat(name, dir_fd=parent, follow_symlinks=False)
        require(count <= limit and stable(opened) == stable(os.fstat(fd))
                and stable(opened) == stable(current), name + ': changed while reading')
        require(text(data), name + ': not UTF-8 text')
        return data
    finally:
        os.close(fd)


def read_regular(path, limit):
    parent, leaf = os.path.split(os.path.abspath(path))
    with directory_fd(parent) as fd:
        return read_at(fd, leaf, limit)


def validate_policy(policy):
    object_fields(policy, ('version', 'distributed', 'maintenance'))
    require(integer(policy['version']) and policy['version'] == 1
            and strings(policy['distributed']) and 0 < len(policy['distributed']) <= MAX_FILES
            and strings(policy['maintenance']),
            'policy needs version 1 and bounded explicit distributed files')
    seen = set()
    for name in policy['distributed']:
        require(valid_path(name) and name.lower() != MANIFEST and name.lower() not in seen,
                'invalid distributed declaration: ' + name)
        seen.add(name.lower())
    for name in policy['maintenance']:
        clean = name[:-1] if name.endswith('/') else name
        require((clean == '.git' or valid_path(clean)) and clean.lower() not in seen
                and clean.lower() != MANIFEST, 'invalid maintenance declaration: ' + name)
        seen.add(clean.lower())
        for distributed in policy['distributed']:
            a, b = distributed.lower(), clean.lower()
            require(not (a == b or a.startswith(b + '/') or b.startswith(a + '/')),
                    'overlapping maintenance declaration: ' + name)
    return policy


def load_policy(path):
    return validate_policy(decode(read_regular(path, MAX_MANIFEST)))


def excluded(name, policy):
    return any(name == item.rstrip('/') or item.endswith('/') and name.startswith(item)
               for item in policy['maintenance'])


@dataclass
class Snapshot:
    files: list = field(default_factory=list)
    content: dict = field(default_factory=dict)
    manifest: bytes = b''


def scan(root, policy):
    validate_policy(policy)
    canonical_root(root)
    snapshot = Snapshot()
    expected = set(policy['distributed'])
    directories = set()
    for name in expected:
        parent = os.path.dirname(name)
        while parent:
            directories.add(parent)
            parent = os.path.dirname(parent)
    aliases, counts = {}, [0, 0]

    def walk(fd, prefix=''):
        before = os.fstat(fd)
        # listdir(fd) and all opens/stats are anchored to the opened directory.
        # No path-based traversal can follow a replaced parent into another tree.
        names = os.listdir(fd)
        require(len(names) <= MAX_ENTRIES, 'filesystem entry limit exceeded')
        for leaf in sorted(names):
            name = prefix + leaf
            counts[0] += 1
            require(counts[0] <= MAX_ENTRIES, 'filesystem entry limit exceeded')
            if excluded(name, policy):
                continue
            require(valid_path(name), 'invalid path: ' + repr(name))
            require(name.lower() not in aliases, 'case alias: ' + name)
            aliases[name.lower()] = name
            info = os.stat(leaf, dir_fd=fd, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode):
                require(name in directories, 'unexpected or empty directory: ' + name)
                with directory_fd(leaf, fd) as child:
                    require(identity(info) == identity(os.fstat(child)),
                            'directory identity changed: ' + name)
                    walk(child, name + '/')
            else:
                require(name in expected or name == MANIFEST,
                        'unexpected distributed file: ' + name)
                data = read_at(fd, leaf, MAX_MANIFEST if name == MANIFEST else MAX_FILE)
                counts[1] += len(data)
                require(counts[1] <= MAX_TOTAL, 'total size limit exceeded')
                if name == MANIFEST:
                    snapshot.manifest = data
                else:
                    snapshot.content[name] = data
        require(stable(before) == stable(os.fstat(fd)), 'directory changed while scanning')

    with directory_fd(root) as fd:
        walk(fd)
    require(expected == set(snapshot.content),
            'missing distributed files: ' + ', '.join(sorted(expected - set(snapshot.content))))
    snapshot.files = [{'path': name, 'sha256': digest(data)}
                      for name, data in sorted(snapshot.content.items())]
    encode(snapshot.files)
    return snapshot


def encode(files):
    require(isinstance(files, list) and 0 < len(files) <= MAX_FILES,
            'inventory count limit exceeded')
    output, previous, aliases, seen = [], '', {}, set()
    for entry in files:
        object_fields(entry, ('path', 'sha256'))
        name, hashed = entry['path'], entry['sha256']
        require(valid_path(name) and name.lower() != MANIFEST and name > previous
                and isinstance(hashed, str) and HASH.fullmatch(hashed),
                'invalid or unsorted inventory')
        parent = name
        while parent:
            key = parent.lower()
            require(key not in aliases or aliases[key] == parent,
                    'case-colliding inventory directories or files')
            require(parent == name or key not in seen, 'inventory file/directory collision')
            aliases[key] = parent
            parent = os.path.dirname(parent)
        require(name.lower() not in seen, 'duplicate inventory file')
        seen.add(name.lower())
        previous = name
        output.append(hashed + '  ' + name + '\n')
    return ''.join(output).encode('ascii')


def validate_snapshot(snapshot):
    encoded = encode(snapshot.files)
    require(isinstance(snapshot.manifest, bytes) and len(snapshot.manifest) <= MAX_MANIFEST
            and text(snapshot.manifest), 'invalid manifest text or size')
    total = len(snapshot.manifest)
    actual = []
    for name, data in sorted(snapshot.content.items()):
        require(isinstance(data, bytes) and len(data) <= MAX_FILE and text(data),
                'invalid snapshot text: ' + name)
        total += len(data)
        actual.append({'path': name, 'sha256': digest(data)})
    require(total <= MAX_TOTAL, 'total size limit exceeded')
    require(encode(actual) == encoded, 'snapshot bytes do not match inventory')


def check(snapshot, inventory):
    validate_snapshot(snapshot)
    require(encode(snapshot.files) == inventory,
            'inventory mismatch: missing, extra or tampered content; review changes before update')


def check_layout(snapshot):
    layout = object_fields(decode(snapshot.content.get('crewbook.json', b'')),
                           ('schema_version', 'name', 'license', 'entrypoints',
                            'resources', 'host_dependencies'))
    entry = object_fields(layout['entrypoints'], ('skill', 'roles', 'claude_agents', 'claude_commands'))
    require(integer(layout['schema_version']) and layout['schema_version'] == 1
            and isinstance(layout['name'], str) and IDENTIFIER.fullmatch(layout['name'])
            and layout['license'] == 'EUPL-1.2' and isinstance(entry['skill'], str)
            and all(strings(entry[key]) for key in ('roles', 'claude_agents', 'claude_commands'))
            and strings(layout['resources']) and isinstance(layout['host_dependencies'], list),
            'incomplete crewbook v1 layout')
    required = [entry['skill']] + entry['roles'] + entry['claude_agents'] + entry['claude_commands'] + layout['resources']
    seen = set()
    for name in required:
        require(valid_path(name) and name not in seen, 'invalid or duplicate layout path: ' + name)
        seen.add(name)
        require(name in snapshot.content, 'missing layout resource: ' + name)
    require(set(snapshot.content) == seen, 'distributed file not declared in crewbook.json')
    for dependency in layout['host_dependencies']:
        object_fields(dependency, ('name', 'scope', 'status'), ('paths',))
        require(all(isinstance(dependency[key], str) and dependency[key]
                    for key in ('name', 'scope', 'status')),
                'host dependencies require name, scope and status')
        paths = dependency.get('paths', [])
        require(strings(paths), 'host dependency paths must be strings')
        for name in paths:
            require(valid_path(name) and name not in seen,
                    'host dependency paths must be explicit, unique and outside bundled set')
            seen.add(name)


def inventory_lines(data):
    require(0 < len(data) <= MAX_INVENTORY and data.endswith(b'\n'),
            'inventory must contain canonical hash lines with a final LF')
    try:
        lines = data.decode('ascii')[:-1].split('\n')
    except UnicodeDecodeError as error:
        raise PackageError('not a canonical inventory file') from error
    files = []
    for line in lines:
        require(len(line) >= 67 and line[64:66] == '  ', 'not a canonical inventory file')
        files.append({'path': line[66:], 'sha256': line[:64]})
    require(encode(files) == data, 'not a canonical inventory file')


def reject_collision(output, protected):
    canonical = os.path.join(os.path.realpath(os.path.dirname(os.path.abspath(protected))),
                             os.path.basename(protected))
    require(output.lower() != canonical.lower(), 'inventory output collides with protected source or policy file')
    if os.path.exists(output) and os.path.exists(protected):
        require(not os.path.samefile(output, protected), 'inventory output aliases protected source or policy file')


def write_inventory(root, path, policy_path, policy, data):
    canonical_root(root)
    validate_policy(policy)
    inventory_lines(data)
    absolute = os.path.abspath(path)
    parent, leaf = os.path.split(absolute)
    require(os.path.realpath(parent) == parent, 'inventory output parent must be canonical without symlink aliases')
    relative = os.path.relpath(absolute, root)
    if relative != '..' and not relative.startswith('../'):
        require(relative.lower().startswith('tools/') and excluded(relative, policy),
                'inventory output inside source must be excluded under tools/')
    for name in [MANIFEST] + policy['distributed']:
        reject_collision(absolute, os.path.join(root, name))
    reject_collision(absolute, policy_path)
    with directory_fd(parent) as fd:
        def validate_target():
            try:
                info = os.stat(leaf, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                return None
            require(stat.S_ISREG(info.st_mode), 'inventory destination must be a regular file without symlink aliases')
            inventory_lines(read_at(fd, leaf, MAX_INVENTORY))
            return stable(info)
        before = validate_target()
        temporary = '.inventory-' + os.urandom(16).hex()
        handle = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=fd)
        try:
            with os.fdopen(handle, 'wb') as output:
                output.write(data)
                output.flush()
                os.fchmod(output.fileno(), 0o644)
                os.fsync(output.fileno())
            require(validate_target() == before, 'inventory destination changed while writing')
            os.replace(temporary, leaf, src_dir_fd=fd, dst_dir_fd=fd)
        finally:
            try:
                os.unlink(temporary, dir_fd=fd)
            except FileNotFoundError:
                pass


def binding(value):
    object_fields(value, ('name', 'version', 'model', 'effort'))
    require(all(isinstance(value[key], str) for key in value), 'invalid explicit client binding')
    require(IDENTIFIER.fullmatch(value['name']) is not None
            and all(0 < len(value[key].encode('utf-8')) <= limit
                    for key, limit in (('version', 128), ('model', 128), ('effort', 32)))
            and not any(c in value['version'] + value['model'] + value['effort'] for c in '\r\n\0'),
            'invalid explicit client binding')
    return value


def runtime_check(snapshot, pin, supported, inputs):
    require(snapshot.manifest, 'missing workharbor.json: source validation is not runtime compatibility; no approved native tuple yet')
    object_fields(pin, ('identity', 'source', 'commit', 'manifest_sha256', 'inventory_sha256', 'contract_version'))
    require(integer(pin['contract_version']) and pin['contract_version'] == 1
            and all(isinstance(pin[key], str) for key in pin if key != 'contract_version')
            and IDENTIFIER.fullmatch(pin['identity']) and COMMIT.fullmatch(pin['commit'])
            and HASH.fullmatch(pin['manifest_sha256']) and HASH.fullmatch(pin['inventory_sha256'])
            and 0 < len(pin['source'].encode('utf-8')) <= 2048
            and not any(c in pin['source'] for c in '\r\n\0'), 'invalid external six-field v1 pin')
    manifest = object_fields(decode(snapshot.manifest), ('contract_version', 'identity', 'entrypoint', 'required_project_inputs', 'adapters', 'files'))
    encoded = encode(manifest['files'])
    require(integer(manifest['contract_version']) and manifest['contract_version'] == 1
            and manifest['identity'] == pin['identity']
            and digest(snapshot.manifest) == pin['manifest_sha256']
            and digest(encoded) == pin['inventory_sha256'] and valid_path(manifest['entrypoint']),
            'manifest does not match external pin')
    check(snapshot, encoded)
    require(manifest['entrypoint'] in snapshot.content, 'entrypoint is not inventoried')
    require(strings(manifest['required_project_inputs']) and len(manifest['required_project_inputs']) <= 32
            and isinstance(manifest['adapters'], list) and 0 < len(manifest['adapters']) <= 32,
            'manifest requires bounded explicit inputs and adapters')
    require(strings(inputs) and isinstance(supported, list), 'invalid provider assertions')
    for value in supported:
        binding(value)
    seen = set()
    for value in manifest['required_project_inputs']:
        require(IDENTIFIER.fullmatch(value) and value not in seen and value in inputs,
                'invalid, duplicate or unconfirmed project input: ' + value)
        seen.add(value)
    seen = set()
    for value in manifest['adapters']:
        binding(value)
        require(value['name'] not in seen, 'duplicate client binding')
        seen.add(value['name'])
        require(value in supported, 'unsupported exact native client version/model/effort tuple for ' + value['name'])


def export(snapshot, destination):
    validate_snapshot(snapshot)
    absolute = os.path.abspath(destination)
    parent, leaf = os.path.split(absolute)
    require(os.path.realpath(parent) == parent, 'export parent must be canonical without symlink aliases')
    with directory_fd(parent) as fd:
        require(not os.path.lexists(absolute), 'export destination must not exist')
        temporary = '.crewbook-export-' + os.urandom(16).hex()
        os.mkdir(temporary, 0o700, dir_fd=fd)
        # Pin every directory and use fd-relative opens, including for cleanup.
        def remove_tree(parent_fd, name):
            with directory_fd(name, parent_fd) as tree:
                for child in os.listdir(tree):
                    info = os.stat(child, dir_fd=tree, follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):
                        remove_tree(tree, child)
                    else:
                        os.unlink(child, dir_fd=tree)
            os.rmdir(name, dir_fd=parent_fd)
        try:
            content = dict(snapshot.content)
            if snapshot.manifest:
                content[MANIFEST] = snapshot.manifest
            with directory_fd(temporary, fd) as stage:
                def write_resource(parent_fd, parts, data):
                    if len(parts) == 1:
                        out = os.open(parts[0], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                      0o400, dir_fd=parent_fd)
                        with os.fdopen(out, 'wb') as handle:
                            handle.write(data)
                        return
                    try:
                        os.mkdir(parts[0], 0o700, dir_fd=parent_fd)
                    except FileExistsError:
                        pass
                    with directory_fd(parts[0], parent_fd) as child:
                        write_resource(child, parts[1:], data)
                for name, data in sorted(content.items()):
                    write_resource(stage, name.split('/'), data)
            # Reserve the destination atomically so even a concurrent empty
            # directory cannot be silently overwritten by rename.
            os.mkdir(leaf, 0o700, dir_fd=fd)
            reserved = os.stat(leaf, dir_fd=fd, follow_symlinks=False)
            try:
                require(identity(reserved) == identity(os.stat(leaf, dir_fd=fd, follow_symlinks=False)),
                        'export destination changed during reservation')
                os.rename(temporary, leaf, src_dir_fd=fd, dst_dir_fd=fd)
            except BaseException:
                if identity(reserved) == identity(os.stat(leaf, dir_fd=fd, follow_symlinks=False)):
                    os.rmdir(leaf, dir_fd=fd)
                raise
        finally:
            try:
                os.stat(temporary, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                remove_tree(fd, temporary)
