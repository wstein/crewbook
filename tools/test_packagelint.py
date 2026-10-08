"""Fixtures for the optional preamble-parity and duplicate-rule lint."""
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest

import packagelint as lint

ROOT = Path(__file__).resolve().parent.parent
PRE = '# CrewBook {}\n\nRead [SKILL.md](../SKILL.md),\nand [team.md](../docs/team.md).\nOwn line {}.\n'
RULE = ' '.join('rule%d' % i for i in range(lint.MIN_WORDS))


def tree(**changes):
    files = {'.agents/crewbook-%s.md' % n: PRE.format(n, n).encode() for n in ('a', 'b', 'c')}
    files['docs/team.md'] = b'# Team\n\nUnrelated short text.\n'
    files.update({k: v.encode() for k, v in changes.items()})
    return files


class LintTests(unittest.TestCase):
    def test_clean_tree(self):
        self.assertEqual(lint.lint(tree()), [])

    def test_preamble_drift_reports_file_and_line(self):
        bad = PRE.format('b', 'b').replace('Read [SKILL', 'Skim [SKILL')
        found = lint.lint(tree(**{'.agents/crewbook-b.md': bad}))
        self.assertEqual(len(found), 1)
        self.assertIn('.agents/crewbook-b.md:3', found[0])
        self.assertIn('preamble', found[0])

    def test_duplicate_rule_reports_both_locations(self):
        found = lint.lint(tree(**{'docs/team.md': '# Team\n\n' + RULE + '\n',
                                  '.agents/crewbook-c.md': PRE.format('c', 'c') + '\n' + RULE.replace(' ', '\n') + '\n'}))
        self.assertEqual(len(found), 1)
        self.assertIn('docs/team.md:3', found[0])
        self.assertIn('.agents/crewbook-c.md:7', found[0])

    def test_shared_preamble_is_not_a_duplicate_rule(self):
        pre = '# CrewBook {}\n\n' + RULE + '\nmore words here.\n\nOwn line {}.\n'
        files = {'.agents/crewbook-%s.md' % n: pre.format(n, n).encode() for n in ('a', 'b')}
        self.assertEqual(lint.lint(files), [])

    def test_short_paragraph_is_ignored(self):
        short = ' '.join(RULE.split()[:lint.MIN_WORDS - 1])
        files = tree(**{'docs/team.md': short + '\n', '.agents/crewbook-c.md': PRE.format('c', 'c') + '\n' + short + '\n'})
        self.assertEqual(lint.lint(files), [])

    def test_cli_flag_is_optional_and_warns(self):
        spec = importlib.util.spec_from_file_location('cli', ROOT / 'tools/crewbook-package.py')
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        out, err = io.StringIO(), io.StringIO()
        cli.run(['check', '--root', str(ROOT)], out, err)
        self.assertNotIn('lint', err.getvalue())
        err = io.StringIO()
        cli.run(['check', '--lint', '--root', str(ROOT)], out, err)
        self.assertIn('lint', err.getvalue())

    def test_lint_rejected_for_other_commands(self):
        spec = importlib.util.spec_from_file_location('cli', ROOT / 'tools/crewbook-package.py')
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        with self.assertRaises(cli.PackageError):
            cli.run(['inventory', '--lint', '--root', str(ROOT)], io.StringIO(), io.StringIO())


if __name__ == '__main__':
    unittest.main()
