"""Structure guards for the CI workflows (text checks; no YAML parser in the stdlib)."""
import re
import unittest
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parent.parent / '.github' / 'workflows'


def read(name):
    return (WORKFLOWS / name).read_text(encoding='utf-8')


def trigger_block(text):
    match = re.search(r'^on:\n((?:[ \t]+.*\n|\n)*)', text, re.M)
    assert match, 'no on: block'
    return match.group(1)


class CheckWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text = read('check.yml')

    def test_push_runs_only_on_main(self):
        # A topic-branch push and its pull_request would run the same SHA twice.
        self.assertRegex(trigger_block(self.text),
                         r'(?m)^  push:\n    branches: \[main\]\n')

    def test_pull_request_still_runs(self):
        self.assertRegex(trigger_block(self.text), r'(?m)^  pull_request:\n')

    def test_concurrency_cancels_superseded_runs(self):
        self.assertRegex(self.text, r'(?m)^concurrency:\n  group: .*github\.ref.*\n'
                                    r'  cancel-in-progress: true\n')


class RequiredCheckTests(unittest.TestCase):
    """The ruleset requires analyze, package (macos-15), package (ubuntu-latest) and
    secrets by name. A required job that never starts or is renamed blocks every PR."""

    def test_required_check_names_exist(self):
        check = read('check.yml')
        self.assertRegex(check, r'(?m)^  package:\n')
        self.assertRegex(check, r'os: \[ubuntu-latest, macos-15\]')
        self.assertRegex(check, r'(?m)^  secrets:\n')
        self.assertRegex(read('codeql.yml'), r'(?m)^  analyze:\n')

    def test_no_path_filters_or_job_conditions(self):
        for name in ('check.yml', 'codeql.yml'):
            text = read(name)
            self.assertNotRegex(text, r'(?m)^\s+paths(-ignore)?:', name)
            self.assertNotRegex(text, r'(?m)^    if:', name)

    def test_main_push_and_schedule_keep_running(self):
        self.assertRegex(trigger_block(read('codeql.yml')),
                         r'(?m)^  push:\n    branches: \[main\]\n')
        self.assertIn('schedule:', trigger_block(read('codeql.yml')))


if __name__ == '__main__':
    unittest.main()
