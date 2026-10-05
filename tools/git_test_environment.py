"""Minimal credential-free environment for offline Git test subprocesses."""
import os
import tempfile


def isolated_git_environment():
    return {
        'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
        'TMPDIR': tempfile.gettempdir(),
        'GIT_CONFIG_SYSTEM': '/dev/null', 'GIT_CONFIG_GLOBAL': '/dev/null',
        'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_COUNT': '1',
        'GIT_CONFIG_KEY_0': 'credential.helper', 'GIT_CONFIG_VALUE_0': '',
        'SSH_AUTH_SOCK': '', 'GIT_SSH_COMMAND': 'ssh -oBatchMode=yes -oIdentityAgent=none',
        'GIT_AUTHOR_NAME': 'Scanner Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
        'GIT_COMMITTER_NAME': 'Scanner Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid',
    }
