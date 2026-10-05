"""Source-only local main guard; installation requires explicit operator approval."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

FILES = {'reference-transaction': 'tools/git-hooks/reference-transaction',
         'source_linear_history.py': 'tools/source_linear_history.py'}


def isolated_git_environment():
    """Explicit credential-free environment; no inherited Git configuration."""
    return {
        'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
        'TMPDIR': tempfile.gettempdir(),
        'GIT_CONFIG_SYSTEM': '/dev/null', 'GIT_CONFIG_GLOBAL': '/dev/null',
        'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_COUNT': '1',
        'GIT_CONFIG_KEY_0': 'credential.helper', 'GIT_CONFIG_VALUE_0': '',
        'SSH_AUTH_SOCK': '',
        'GIT_SSH_COMMAND': 'ssh -oBatchMode=yes -oIdentityAgent=none',
    }


def git(*args, root=None, gitdir=None, allow_failure=False):
    command = ['git', '--no-replace-objects']
    if gitdir is not None:
        command.append('--git-dir=' + str(gitdir))
    if root is not None:
        command += ['-C', str(root)]
    command += list(args)
    result = subprocess.run(command, env=isolated_git_environment(), capture_output=True)
    if result.returncode and not allow_failure:
        raise ValueError('Git operation failed: ' + ' '.join(args[:2]))
    return result


def check(phase):
    if phase != 'prepared':
        return
    repository = bound_repository()

    def read(*args, allow_failure=False):
        return git(*args, gitdir=repository, allow_failure=allow_failure)

    for line in sys.stdin:
        fields = line.split()
        if len(fields) != 3:
            raise ValueError('malformed reference transaction')
        old, new, ref = fields
        if ref != 'refs/heads/main':
            continue
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', old) or len(old) != len(new) or not re.fullmatch(r'[0-9a-f]+', new):
            raise ValueError('invalid main object identifiers')
        if set(new) == {'0'}:
            raise ValueError('main deletion refused')
        symbolic = read('symbolic-ref', '-q', 'refs/heads/main', allow_failure=True)
        if symbolic.returncode != 1:
            raise ValueError('main must be a direct reference')
        current = read('rev-parse', '--verify', 'refs/heads/main').stdout.decode().strip()
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', current) or len(current) != len(old):
            raise ValueError('invalid current main object identifier')
        if read('cat-file', '-t', current).stdout.strip() != b'commit':
            raise ValueError('main must name a commit')
        if set(old) != {'0'} and old != current:
            raise ValueError('transaction old main differs from current main')
        old = current
        if read('cat-file', '-t', new).stdout.strip() != b'commit':
            raise ValueError('candidate main must name a commit')
        if read('rev-parse', '--is-shallow-repository').stdout.strip() != b'false':
            raise ValueError('shallow history cannot establish main ancestry')
        grafts = Path(read('rev-parse', '--git-path', 'info/grafts').stdout.decode().strip())
        if grafts.exists() or grafts.is_symlink():
            raise ValueError('legacy grafts cannot establish physical main history')
        if read('merge-base', '--is-ancestor', old, new, allow_failure=True).returncode:
            raise ValueError('main update must be a fast-forward')
        if read('rev-list', '--max-count=1', '--min-parents=2', old + '..' + new).stdout.strip():
            raise ValueError('main update introduces a merge commit')


def safe_directory(path):
    """Reject links and writable-by-others ancestors before private writes."""
    for item in [path] + list(path.parents):
        info = item.lstat()
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError('directory path contains a link or non-directory')
        # Shared system temporary ancestors may be sticky, never the destination.
        if info.st_mode & 0o022 and not (item != path and info.st_mode & stat.S_ISVTX):
            raise ValueError('directory path is writable by others')
    if path.stat().st_uid != os.getuid():
        raise ValueError('destination directory is not owned by this user')


def context(root, revision):
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', revision):
        raise ValueError('full exact reviewed commit SHA required')
    if git('rev-parse', '--verify', revision + '^{commit}', root=root).stdout.decode().strip() != revision:
        raise ValueError('revision is not the exact commit SHA')
    # Relative common-dir results are relative to the requested repository.
    raw = Path(git('rev-parse', '--git-common-dir', root=root).stdout.decode().strip())
    common = raw if raw.is_absolute() else Path(os.path.abspath(str(root / raw)))
    safe_directory(common)
    blobs = {name: git('show', revision + ':' + source, root=root).stdout for name, source in FILES.items()}
    if Path(__file__).read_bytes() != blobs['source_linear_history.py']:
        raise ValueError('running installer differs from reviewed revision')
    return common, blobs


def installed(directory, blobs):
    safe_directory(directory)
    if set(p.name for p in directory.iterdir()) != set(blobs):
        raise ValueError('installed directory contains unexpected entries')
    for name, content in blobs.items():
        path = directory / name
        info = path.lstat()
        expected = 0o500 if name == 'reference-transaction' else 0o400
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != expected or path.read_bytes() != content:
            raise ValueError('installed reviewed bytes or permissions differ')


def bound_repository():
    """Bind hook reads to its installed common Git directory, never hook cwd."""
    source = Path(__file__).absolute()
    directory = source.parent
    revision = directory.name
    if source.name != 'source_linear_history.py' or directory.parent.name != 'crewbook-source-guards':
        raise ValueError('check requires the reviewed installed guard layout')
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', revision):
        raise ValueError('installed guard version is not a full commit SHA')
    common = directory.parent.parent
    safe_directory(common)
    blobs = {name: git('show', revision + ':' + path, gitdir=common).stdout
             for name, path in FILES.items()}
    installed(directory, blobs)
    return common


def install_or_verify(root, revision, activate, confirmed):
    common, blobs = context(root, revision)
    parent = common / 'crewbook-source-guards'
    destination = parent / revision
    configured = git('config', '--local', '--get-all', 'core.hooksPath', root=root, allow_failure=True)
    if configured.returncode not in (0, 1):
        raise ValueError('cannot inspect local hooks configuration')
    value = configured.stdout.decode().splitlines()
    if value and value != [str(destination)]:
        raise ValueError('existing local hooksPath is preserved; installation refused')
    worktree_config = git('config', '--local', '--get', 'extensions.worktreeConfig', root=root, allow_failure=True)
    if worktree_config.returncode == 0:
        raise ValueError('worktree-specific configuration requires separate operator review')
    if activate:
        if not confirmed:
            raise ValueError('operator confirmation of effective hook routing is required')
        defaults = common / 'hooks'
        if defaults.exists():
            safe_directory(defaults)
            if any(not p.name.endswith('.sample') for p in defaults.iterdir()):
                raise ValueError('existing default hooks are preserved; installation refused')
        if not parent.exists():
            parent.mkdir(mode=0o700)
        safe_directory(parent)
        if not destination.exists():
            destination.mkdir(mode=0o700)
            for name, content in blobs.items():
                with (destination / name).open('xb') as stream:
                    stream.write(content)
                (destination / name).chmod(0o500 if name == 'reference-transaction' else 0o400)
        installed(destination, blobs)
        git('config', '--local', 'core.hooksPath', str(destination), root=root)
    else:
        if value != [str(destination)]:
            raise ValueError('reviewed guard is not configured locally')
        installed(destination, blobs)
    print('Local reviewed guard: ' + revision)
    for name, content in blobs.items():
        print(name + ' sha256 ' + hashlib.sha256(content).hexdigest())
    print('Effective system/global/command hook routing remains operator-confirmed, not inspected.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'install', 'verify'])
    parser.add_argument('phase', nargs='?')
    parser.add_argument('--root', type=Path)
    parser.add_argument('--reviewed-sha')
    parser.add_argument('--confirm-effective-hook-routing', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'check':
            if args.phase not in ('preparing', 'prepared', 'committed', 'aborted'):
                raise ValueError('unknown transaction phase')
            check(args.phase)
        else:
            if args.root is None or args.reviewed_sha is None:
                raise ValueError('--root and --reviewed-sha required')
            install_or_verify(args.root.absolute(), args.reviewed_sha, args.command == 'install', args.confirm_effective_hook_routing)
    except (OSError, ValueError) as error:
        print('source main guard: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
