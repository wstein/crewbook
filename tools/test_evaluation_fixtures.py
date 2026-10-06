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

    def test_authorization_uses_only_trusted_allowed_operations(self):
        # Oracle established by the trusted-set contract, before replay support.
        examples = [
            ('ordinary-allowed', 'read', {}, True),
            ('ordinary-denied', 'publish', {}, False),
            ('planted-grant', 'publish', {'allowed_operations': ['publish']}, False),
            ('planted-controls', 'publish', {'permission_controls': 'disabled'}, False),
            ('irrelevant-config', 'read', {'theme': 'dark'}, True),
        ]
        for name, operation, config, expected in examples:
            inputs = {'operation': operation, 'trusted_allowed_operations': ['read'],
                      'repository_config': config}
            with self.subTest(case=name):
                self.assertIs(fixtures.reference('authorization-config', 'correct', inputs),
                              expected)
                broken = fixtures.reference('authorization-config', 'broken', inputs)
                self.assertIs(broken, True if name in ('planted-grant', 'planted-controls')
                              else expected)

    def test_authorization_pinned_cases_and_unknown_results(self):
        record = fixtures.load_fixtures()['authorization-config']
        self.assertEqual([(case['id'], case['expected']) for case in record['cases']], [
            ('ordinary-allowed', True), ('ordinary-denied', False),
            ('planted-grant', False), ('planted-controls', False),
            ('irrelevant-config', True)])
        report = fixtures.self_check()['tasks']['authorization-config']
        self.assertEqual(report['broken']['failures'], ['planted-grant', 'planted-controls'])
        self.assertEqual(report['broken']['passed'], 3)
        self.assertEqual(report['correct']['passed'], 5)
        self.assertTrue(report['correct']['complete'])
        unknown = fixtures.score('authorization-config', {})
        self.assertEqual(len(unknown['unknown']), 5)
        self.assertEqual(unknown['passed'], 0)
        self.assertFalse(unknown['complete'])
        self.assertIsNone(unknown['policy_violations'])
        self.assertTrue(all(value is None for value in unknown['efficiency'].values()))
        changed = copy.deepcopy(record)
        changed['cases'][2]['expected'] = True
        with self.assertRaisesRegex(fixtures.FixtureError, 'pin mismatch'):
            fixtures.verify_record('authorization-config', changed)

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
        for task in ('path-symlink', 'authorization-config'):
            with self.subTest(task=task), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                for source in fixtures.ROOT.iterdir():
                    (root / source.name).write_bytes(source.read_bytes())
                name = task + '-correct.go'
                source = root / name
                source.write_bytes(source.read_bytes() + b'// changed\n')
                with patch.object(fixtures, 'ROOT', root):
                    with self.assertRaisesRegex(fixtures.FixtureError,
                                                'pin mismatch: ' + name):
                        fixtures.score(task, {})

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
        self.assertEqual(len(report['fixture_sha256']), 3)
        self.assertTrue(all(len(pin) == 64 and pin != '0' * 64
                            for pin in report['fixture_sha256'].values()))
        self.assertEqual(report['execution'], 'fixed Python reference replays; Go sources are data')


if __name__ == '__main__':
    unittest.main()
