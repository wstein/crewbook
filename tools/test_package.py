"""Offline behaviour and failure fixtures for the stock-Python maintenance CLI."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import packagefmt as pkg

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('crewbook_cli', ROOT / 'tools/crewbook-package.py')
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'source'
        self.root.mkdir()
        self.policy = {'version': 1, 'distributed': ['.agents/role.md', 'LICENSE', 'SKILL.md', 'crewbook.json'],
                       'maintenance': ['tools/']}
        layout = {'schema_version': 1, 'name': 'crewbook', 'license': 'EUPL-1.2',
                  'entrypoints': {'skill': 'SKILL.md', 'roles': ['.agents/role.md'],
                                 'claude_agents': [], 'claude_commands': []},
                  'resources': ['crewbook.json', 'LICENSE'], 'host_dependencies': []}
        for name in self.policy['distributed']:
            self.write(name, ('text ' + name + '\n').encode())
        self.write('crewbook.json', json.dumps(layout).encode())
        self.write('tools/package-policy.json', json.dumps(self.policy).encode())
        self.write('tools/export-policy.json', json.dumps(dict(self.policy, maintenance=[])).encode())

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o644)

    def scan(self):
        return pkg.scan(str(self.root), self.policy)

    def invoke(self, command, *args):
        out, err = io.StringIO(), io.StringIO()
        cli.run([command, '--root', str(self.root)] + list(args), out, err)
        return out.getvalue(), err.getvalue()

    def test_cli_roundtrip_and_tamper(self):
        with self.assertRaises(FileNotFoundError):
            self.invoke('check')
        expected, _ = self.invoke('inventory')
        self.invoke('update')
        self.assertEqual((self.root / 'tools/package.sha256').read_text(), expected)
        self.invoke('update')
        self.assertEqual(self.invoke('check')[0], '')
        self.assertIn('runtime compatibility not established', self.invoke('check')[1])
        self.write('SKILL.md', b'tampered')
        with self.assertRaisesRegex(pkg.PackageError, 'inventory mismatch'):
            self.invoke('check')

    def test_cli_does_not_execute_or_parse_prompts(self):
        marker = self.base / 'never-created'
        self.write('SKILL.md', ('[bad](missing.md)\n```sh\ntouch ' + str(marker) + '\n```\n').encode())
        self.invoke('update')
        self.invoke('check')
        self.assertFalse(marker.exists())

    def test_inventory_exact_encoding(self):
        snap = self.scan()
        expected = b''.join(pkg.digest(snap.content[name]).encode() + b'  ' + name.encode() + b'\n'
                            for name in sorted(self.policy['distributed']))
        self.assertEqual(pkg.encode(snap.files), expected)
        self.assertEqual(pkg.encode(self.scan().files), expected)

    def test_export_relocation_and_exact_boundary(self):
        self.invoke('update')
        destination = self.base / 'export'
        self.invoke('export', '--dest', str(destination))
        self.assertFalse((destination / 'tools').exists())
        for name in self.policy['distributed']:
            self.assertEqual((destination / name).read_bytes(), (self.root / name).read_bytes())
            self.assertEqual((destination / name).stat().st_mode & 0o777, 0o400)
        relocated = self.base / 'relocated'
        destination.rename(relocated)
        args = ['check', '--root', str(relocated), '--policy', str(self.root / 'tools/export-policy.json'),
                '--inventory', str(self.root / 'tools/package.sha256')]
        cli.run(args, io.StringIO(), io.StringIO())
        (relocated / '.extra').write_text('extra')
        with self.assertRaises(pkg.PackageError):
            cli.run(args)

    def test_export_refuses_existing_and_forged_snapshot(self):
        snap = self.scan()
        dest = self.base / 'export'
        dest.mkdir()
        with self.assertRaisesRegex(pkg.PackageError, 'must not exist'):
            pkg.export(snap, str(dest))
        snap.content['../escape'] = b'bad'
        with self.assertRaises(pkg.PackageError):
            pkg.export(snap, str(self.base / 'other'))
        self.assertFalse((self.base / 'other').exists())

    def test_export_uses_validated_snapshot_bytes(self):
        snap = self.scan()
        self.write('SKILL.md', b'changed after scan')
        dest = self.base / 'snapshot'
        pkg.export(snap, str(dest))
        self.assertEqual((dest / 'SKILL.md').read_bytes(), snap.content['SKILL.md'])

    def test_export_cleans_failure_and_preserves_concurrent_destination(self):
        snap = self.scan()
        dest = self.base / 'export'
        real_mkdir = os.mkdir
        def competing_mkdir(path, mode=0o777, *, dir_fd=None):
            if path == 'export':
                real_mkdir(path, mode, dir_fd=dir_fd)
                raise FileExistsError('concurrent destination')
            return real_mkdir(path, mode, dir_fd=dir_fd)
        with mock.patch.object(pkg.os, 'mkdir', side_effect=competing_mkdir):
            with self.assertRaises(FileExistsError):
                pkg.export(snap, str(dest))
        self.assertTrue(dest.is_dir())
        self.assertFalse(list(self.base.glob('.crewbook-export-*')))

    def test_scan_unsafe_files(self):
        mutations = {
            'missing': lambda p: p.unlink(),
            'symlink': lambda p: (p.unlink(), p.symlink_to('LICENSE')),
            'hardlink': lambda p: (p.unlink(), os.link(self.root / 'LICENSE', p)),
            'executable': lambda p: p.chmod(0o755),
            'world-writable': lambda p: p.chmod(0o666),
            'setuid': lambda p: p.chmod(0o4644),
            'binary': lambda p: p.write_bytes(b'\xff'),
            'nul': lambda p: p.write_bytes(b'\0'),
            'oversize': lambda p: p.write_bytes(b'a' * (pkg.MAX_FILE + 1)),
            'fifo': lambda p: (p.unlink(), os.mkfifo(p, 0o600)),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                p = self.root / 'SKILL.md'
                mutate(p)
                if name == 'setuid' and not (p.lstat().st_mode & 0o4000):
                    # Some macOS volumes strip setuid on non-executable files.
                    self.write('SKILL.md', b'restored\n')
                    continue
                with self.assertRaises((pkg.PackageError, OSError)):
                    self.scan()
                if p.exists() or p.is_symlink():
                    p.unlink()
                self.write('SKILL.md', b'restored\n')

    def test_scan_extra_empty_case_and_directory_permissions(self):
        for name in ('.hidden', 'empty', 'LICENSE.other'):
            with self.subTest(name=name):
                p = self.root / name
                if name == 'empty':
                    p.mkdir()
                else:
                    p.write_bytes(b'extra')
                with self.assertRaises(pkg.PackageError):
                    self.scan()
                p.rmdir() if p.is_dir() else p.unlink()
        (self.root / '.agents').chmod(0o777)
        with self.assertRaisesRegex(pkg.PackageError, 'unsafe directory'):
            self.scan()
        (self.root / '.agents').chmod(0o755)

    def test_read_rejects_file_replacement(self):
        real_open = os.open
        def replace_before_open(name, flags, mode=0o777, *, dir_fd=None):
            if name == 'SKILL.md':
                os.unlink(name, dir_fd=dir_fd)
                fd = real_open(name, os.O_CREAT | os.O_WRONLY, 0o644, dir_fd=dir_fd)
                os.write(fd, b'replacement')
                os.close(fd)
            return real_open(name, flags, mode, dir_fd=dir_fd)
        with mock.patch.object(pkg.os, 'open', side_effect=replace_before_open):
            with self.assertRaisesRegex(pkg.PackageError, 'identity'):
                pkg.read_regular(str(self.root / 'SKILL.md'), pkg.MAX_FILE)

    def test_scan_rejects_directory_replacement(self):
        real_open = os.open
        def replace_before_open(name, flags, mode=0o777, *, dir_fd=None):
            if name == '.agents':
                os.rename('.agents', '.original-agents', src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                os.mkdir('.agents', dir_fd=dir_fd)
            return real_open(name, flags, mode, dir_fd=dir_fd)
        with mock.patch.object(pkg.os, 'open', side_effect=replace_before_open):
            with self.assertRaisesRegex(pkg.PackageError, 'directory changed'):
                self.scan()

    def test_invalid_paths_and_inventory_aliases(self):
        for name in ('../escape', '/absolute', 'a//b', 'a/./b', 'a/../b', 'a\\b', 'a.',
                     'a/.GIT/b', 'a/é', 'a/', 'a b', 'a' * 241, ''):
            self.assertFalse(pkg.valid_path(name), name)
        hashed = pkg.digest(b'fixture')
        for names in (['A', 'a'], ['A/one', 'a/two'], ['a', 'a/child'], ['workharbor.json'], ['b', 'a']):
            with self.assertRaises(pkg.PackageError):
                pkg.encode([{'path': name, 'sha256': hashed} for name in names])
        with self.assertRaises(pkg.PackageError):
            pkg.encode([{'path': 'a', 'sha256': hashed.upper()}])

    def test_policy_errors(self):
        for mutate in (lambda p: p.update(version=True),
                       lambda p: p['distributed'].append('../escape'),
                       lambda p: p['distributed'].append('skill.md'),
                       lambda p: p['maintenance'].append('.agents/'),
                       lambda p: p.update(extra='unknown'),
                       lambda p: p.update(distributed=None)):
            policy = copy.deepcopy(self.policy)
            mutate(policy)
            with self.assertRaises(pkg.PackageError):
                pkg.validate_policy(policy)

    def test_strict_json(self):
        for data in (b'{"a":1,"a":2}', b'{"a":{"b":1,"b":2}}', b'{} {}', b'NaN', b'\xff'):
            with self.assertRaises(pkg.PackageError):
                pkg.decode(data)
        for data in (b'null', b'{"version":1,"distributed":[],"maintenance":[],"unknown":true}'):
            with self.assertRaises(pkg.PackageError):
                pkg.validate_policy(pkg.decode(data))

    def test_layout_constraints(self):
        base = self.scan()
        for mutate in (lambda x: x.update(schema_version=True),
                       lambda x: x.update(executable='bad'),
                       lambda x: x['resources'].append('SKILL.md'),
                       lambda x: x['resources'].append('missing'),
                       lambda x: x['entrypoints'].update(roles=None),
                       lambda x: x['host_dependencies'].append({'name': 'x', 'scope': 'x', 'status': 'x', 'paths': ['LICENSE']})):
            snapshot = copy.deepcopy(base)
            layout = pkg.decode(snapshot.content['crewbook.json'])
            mutate(layout)
            snapshot.content['crewbook.json'] = json.dumps(layout).encode()
            with self.assertRaises(pkg.PackageError):
                pkg.check_layout(snapshot)

    def test_limits(self):
        with self.assertRaises(pkg.PackageError):
            pkg.encode([{}] * (pkg.MAX_FILES + 1))
        snap = pkg.Snapshot()
        for i in range(17):
            name, data = 'file%02d' % i, b'a' * pkg.MAX_FILE
            snap.content[name] = data
            snap.files.append({'path': name, 'sha256': pkg.digest(data)})
        with self.assertRaisesRegex(pkg.PackageError, 'total size'):
            pkg.validate_snapshot(snap)
        self.write('workharbor.json', b'a' * (pkg.MAX_MANIFEST + 1))
        with self.assertRaisesRegex(pkg.PackageError, 'size limit'):
            self.scan()

    def test_noncanonical_roots(self):
        alias = self.base / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        for root in ('.', str(self.root) + '/.', str(alias)):
            with self.assertRaises(pkg.PackageError):
                pkg.scan(root, self.policy)

    def test_update_output_collisions_without_mutation(self):
        self.invoke('update')
        self.write('tools/code.py', b'protected code')
        (self.root / 'tools/link.sha256').symlink_to(self.root / 'SKILL.md')
        os.link(self.root / 'tools/code.py', self.root / 'tools/hardlink.sha256')
        (self.root / 'tools/alias').symlink_to(self.root, target_is_directory=True)
        protected = ['SKILL.md', 'LICENSE', 'crewbook.json', 'tools/package-policy.json',
                     'tools/code.py', 'tools/package.sha256']
        before = {name: (self.root / name).read_bytes() for name in protected}
        for name in [item for item in protected if item != 'tools/package.sha256'] + ['skill.md', 'workharbor.json', 'tools/link.sha256',
                                 'tools/hardlink.sha256', 'tools/alias/out.sha256']:
            with self.subTest(name=name):
                with self.assertRaises((pkg.PackageError, OSError)):
                    self.invoke('update', '--inventory', str(self.root / name))
                for path, data in before.items():
                    self.assertEqual((self.root / path).read_bytes(), data)

    def test_update_custom_inventory(self):
        expected = self.invoke('inventory')[0]
        for dest in (self.root / 'tools/custom.sha256', self.base / 'custom.inventory'):
            for _ in range(2):
                self.invoke('update', '--inventory', str(dest))
                self.assertEqual(dest.read_text(), expected)
                self.invoke('check', '--inventory', str(dest))

    def test_update_cannot_add_exclusions(self):
        data = pkg.encode(self.scan().files)
        policy = dict(self.policy, maintenance=[])
        with self.assertRaises(pkg.PackageError):
            pkg.write_inventory(str(self.root), str(self.root / 'tools/new.sha256'),
                                str(self.root / 'tools/package-policy.json'), policy, data)
        self.assertFalse((self.root / 'tools/new.sha256').exists())

    def runtime_fixture(self):
        snap = self.scan()
        supported = {'name': 'claude-code', 'version': 'fixture-only version',
                     'model': 'fixture-only-model', 'effort': 'fixture-only-effort'}
        manifest = {'contract_version': 1, 'identity': 'crewbook', 'entrypoint': 'SKILL.md',
                    'required_project_inputs': ['project-policy'], 'adapters': [supported], 'files': snap.files}
        snap.manifest = json.dumps(manifest).encode()
        pin = {'contract_version': 1, 'identity': 'crewbook', 'source': 'fixture-only-source',
               'commit': 'a' * 40, 'manifest_sha256': pkg.digest(snap.manifest),
               'inventory_sha256': pkg.digest(pkg.encode(snap.files))}
        return snap, pin, supported

    def test_runtime_exact_bindings_and_pin(self):
        snap, pin, supported = self.runtime_fixture()
        pkg.runtime_check(snap, pin, [supported], ['project-policy'])
        for key in ('version', 'model', 'effort'):
            altered = dict(supported, **{key: 'other'})
            with self.assertRaisesRegex(pkg.PackageError, 'unsupported exact'):
                pkg.runtime_check(snap, pin, [altered], ['project-policy'])
        for altered in (dict(pin, manifest_sha256='0' * 64), dict(pin, identity='a' * 65),
                        dict(pin, contract_version=True), dict(pin, extra='unknown')):
            with self.assertRaises(pkg.PackageError):
                pkg.runtime_check(snap, altered, [supported], ['project-policy'])
        with self.assertRaisesRegex(pkg.PackageError, 'unconfirmed'):
            pkg.runtime_check(snap, pin, [supported], [])

    def test_runtime_manifest_constraints(self):
        for mutate in (lambda m: m.update(adapters=[]), lambda m: m.update(required_project_inputs=None),
                       lambda m: m['required_project_inputs'].append('project-policy'),
                       lambda m: m['adapters'].append(dict(m['adapters'][0])),
                       lambda m: m.update(entrypoint='../escape'),
                       lambda m: m['adapters'][0].update(effort='x' * 33)):
            snap, pin, supported = self.runtime_fixture()
            supported = copy.deepcopy(supported)
            manifest = pkg.decode(snap.manifest)
            mutate(manifest)
            snap.manifest = json.dumps(manifest).encode()
            pin['manifest_sha256'] = pkg.digest(snap.manifest)
            with self.assertRaises(pkg.PackageError):
                pkg.runtime_check(snap, pin, [supported], ['project-policy'])

    def test_runtime_cli_and_missing_manifest(self):
        for command in ('runtime-check', 'lock'):
            with self.assertRaisesRegex(pkg.PackageError, 'missing workharbor.json'):
                self.invoke(command)
        snap, pin, supported = self.runtime_fixture()
        self.write('workharbor.json', snap.manifest)
        provider = self.base / 'provider.json'
        provider.write_text(json.dumps({'bindings': [supported], 'project_inputs': ['project-policy']}))
        out, _ = self.invoke('lock', '--provider', str(provider), '--source', pin['source'], '--commit', pin['commit'])
        self.assertEqual(json.loads(out), pin)
        pin_path = self.base / 'pin.json'
        pin_path.write_text(out)
        self.invoke('runtime-check', '--provider', str(provider), '--pin', str(pin_path))

    def test_cli_subprocess_exit_and_streams(self):
        self.invoke('update')
        for args, expected in ((['check', '--root', str(self.root)], 0),
                               (['runtime-check', '--root', str(self.root)], 1),
                               (['unknown'], 1), (['check'], 1), (['check', '--unknown'], 1)):
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/crewbook-package.py')] + args,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, expected, result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertNotIn('Traceback', result.stderr)

    def test_actual_source_and_export_policy_agree(self):
        source = pkg.load_policy(str(ROOT / 'tools/package-policy.json'))
        exported = pkg.load_policy(str(ROOT / 'tools/export-policy.json'))
        self.assertEqual(source['distributed'], exported['distributed'])
        self.assertEqual(exported['maintenance'], [])
        snapshot = pkg.scan(str(ROOT), source)
        pkg.check_layout(snapshot)
        pkg.check(snapshot, pkg.read_regular(str(ROOT / 'tools/package.sha256'), pkg.MAX_INVENTORY))


if __name__ == '__main__':
    unittest.main()
