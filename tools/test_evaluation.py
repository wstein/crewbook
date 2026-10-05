"""Credential-free scoring checks; synthetic records never execute target code."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import evaluation

FIXTURE = Path(__file__).with_name('evaluation-fixture.json')


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())

    def test_preserves_failures_unknowns_and_quality_before_efficiency(self):
        result = evaluation.summarize(self.data)
        self.assertEqual(result['sample_sizes'], {
            'baseline': {'scored': 1, 'failed': 1, 'missing': 0},
            'guarded': {'scored': 1, 'failed': 0, 'missing': 1}})
        self.assertEqual(result['runs'], self.data['runs'])
        self.assertIsNone(result['runs'][0]['efficiency']['billed_cost_usd'])
        self.assertFalse(result['runs'][0]['outcomes']['criteria']['reject-escape'])
        self.assertEqual(result['runs'][0]['outcomes']['policy_violations'], 1)

    def test_rejects_unmatched_or_duplicate_slots(self):
        for runs in (self.data['runs'][:-1], self.data['runs'] + [self.data['runs'][0]]):
            with self.subTest(runs=len(runs)), self.assertRaises(evaluation.EvidenceError):
                evaluation.summarize(dict(self.data, runs=runs))

    def test_rejects_unlike_bindings(self):
        self.data['runs'][0]['configuration'] = copy.deepcopy(self.data['configuration'])
        self.data['runs'][0]['configuration']['model'] = 'other-model'
        with self.assertRaisesRegex(evaluation.EvidenceError, 'unlike'):
            evaluation.summarize(self.data)

    def test_rejects_invalid_scores_metadata_and_unknown_fields(self):
        mutations = [
            lambda d: d['configuration'].update(repository_revision='unpinned'),
            lambda d: d['tasks'][0].update(fixture_sha256='bad'),
            lambda d: d['runs'][0]['outcomes']['criteria'].update({'reject-escape': 1}),
            lambda d: d['runs'][0]['outcomes'].update(policy_violations=-1),
            lambda d: d['runs'][0]['efficiency'].update(input_tokens=True),
            lambda d: d['runs'][0]['efficiency'].update(billed_cost_usd=float('nan')),
            lambda d: d['runs'][2].update(note=''),
            lambda d: d.update(extra=True),
        ]
        for mutate in mutations:
            data = copy.deepcopy(self.data)
            mutate(data)
            with self.subTest(mutation=mutate), self.assertRaises(evaluation.EvidenceError):
                evaluation.summarize(data)

    def test_cli_and_duplicate_json(self):
        script = FIXTURE.with_name('evaluation.py')
        run = subprocess.run([sys.executable, '-B', str(script), str(FIXTURE)],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout), evaluation.load(FIXTURE))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            path.write_text('{"version":1,"version":1}')
            run = subprocess.run([sys.executable, '-B', str(script), str(path)],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertEqual(run.stdout, '')
            self.assertIn('duplicate JSON field', run.stderr)


if __name__ == '__main__':
    unittest.main()
