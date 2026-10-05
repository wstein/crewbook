"""Independent acceptance expectations for fixed offline evaluation fixtures."""
import copy
import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

import evaluation_fixtures as fixtures


class FixtureTests(unittest.TestCase):
    def test_shared_callers_and_adapter_error_preservation(self):
        report = fixtures.self_check()
        shared = report['tasks']['shared-adapter']
        self.assertEqual(shared['broken']['failures'], [
            'json-trims-space', 'cli-trims-space', 'adapter-preserves-denial'])
        self.assertEqual(shared['correct']['failures'], [])
        self.assertEqual(shared['broken']['passed'], 2)
        self.assertEqual(shared['correct']['passed'], 5)

    def test_security_bug_passes_ordinary_case_but_fails_adversarial_cases(self):
        path = fixtures.self_check()['tasks']['path-symlink']
        self.assertEqual(path['broken']['failures'], [
            'parent-traversal', 'absolute-path', 'sibling-prefix',
            'symlink-leaf', 'symlink-parent', 'nested-traversal'])
        self.assertEqual(path['broken']['passed'], 1)
        self.assertEqual(path['correct']['failures'], [])
        self.assertEqual(path['correct']['passed'], 7)

    def test_hash_pin_detects_changed_bytes(self):
        records = fixtures.load_fixtures()
        changed = copy.deepcopy(records)
        changed['shared-adapter']['cases'][0]['expected'] = 'tampered'
        with self.assertRaisesRegex(fixtures.FixtureError, 'pin mismatch'):
            fixtures.verify_record('shared-adapter', changed['shared-adapter'])

    def test_unknown_never_becomes_a_pass_or_zero_efficiency(self):
        result = fixtures.score('shared-adapter', {'ordinary-json': 'alpha'})
        self.assertEqual(result['passed'], 1)
        self.assertEqual(len(result['unknown']), 4)
        self.assertFalse(result['complete'])
        self.assertIsNone(result['efficiency']['billed_cost_usd'])
        self.assertIsNone(result['human_review_seconds'])

    def test_raw_source_tampering_is_rejected_before_scoring(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for source in fixtures.ROOT.iterdir():
                (root / source.name).write_bytes(source.read_bytes())
            source = root / 'path-symlink-correct.go'
            source.write_bytes(source.read_bytes() + b'// changed\n')
            with patch.object(fixtures, 'ROOT', root):
                with self.assertRaisesRegex(fixtures.FixtureError,
                                            'pin mismatch: path-symlink-correct.go'):
                    fixtures.score('path-symlink', {})

    def test_wrong_boolean_type_fails_with_diagnostic(self):
        result = fixtures.score('path-symlink', {'ordinary-file': 1})
        self.assertEqual(result['failures'], ['ordinary-file'])
        self.assertEqual(result['criteria'][0], {
            'criterion': 'ordinary-file', 'status': 'fail',
            'expected': True, 'observed': 1})
        self.assertFalse(result['complete'])

    def test_unknown_task_and_extra_observation_rejected(self):
        with self.assertRaisesRegex(fixtures.FixtureError, 'unknown task'):
            fixtures.score('other', {})
        with self.assertRaisesRegex(fixtures.FixtureError, 'unexpected observation'):
            fixtures.score('shared-adapter', {'invented': True})

    def test_fixture_sources_are_pinned_data(self):
        report = fixtures.self_check()
        self.assertEqual(len(report['fixture_sha256']), 2)
        self.assertTrue(all(len(pin) == 64 and pin != '0' * 64
                            for pin in report['fixture_sha256'].values()))
        self.assertEqual(report['execution'], 'fixed Python reference replays; Go sources are data')


if __name__ == '__main__':
    unittest.main()
