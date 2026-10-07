"""Review-line grammar and pre-land model gate (modelled; the procedure itself is model-run)."""
import unittest

import review_lines as rl

SHA = 'a' * 40


class ReviewLineTests(unittest.TestCase):
    def test_start_requires_model(self):
        self.assertIsNotNone(rl.parse('review started %s model=opus' % SHA))
        self.assertIsNone(rl.parse('review started %s' % SHA))

    def test_clear_requires_model(self):
        self.assertEqual(rl.parse('CLEAR %s model=gpt-6.1-sol/medium' % SHA),
                         ('CLEAR', SHA, 'gpt-6.1-sol/medium'))
        self.assertIsNone(rl.parse('CLEAR %s' % SHA))
        self.assertIsNone(rl.parse('NOT CLEAR %s model=' % SHA))
        self.assertIsNotNone(rl.parse('NOT CLEAR %s model=opus' % SHA))

    def test_rejects_junk(self):
        for bad in ('CLEAR %s model=o pus' % SHA, 'CLEAR abc model=opus',
                    'CLEAR %s model=opus extra' % SHA):
            self.assertIsNone(rl.parse(bad), bad)

    def test_rejects_doubled_model_key(self):
        self.assertIsNone(rl.parse('CLEAR %s model=model=opus' % SHA))

    def test_gate_meets_required_count(self):
        ok = ['CLEAR %s model=opus' % SHA, 'CLEAR %s model=gpt-6.1-sol/medium' % SHA]
        self.assertEqual(rl.gate(ok, SHA, {'opus', 'gpt-6.1-sol/medium'}, 2), [])
        self.assertEqual(rl.gate(ok[:1], SHA, {'opus'}, 1), [])

    def test_gate_too_few_stamps(self):
        gaps = rl.gate(['CLEAR %s model=opus' % SHA], SHA, {'opus'}, 2)
        self.assertEqual(len(gaps), 1)
        self.assertNotEqual(rl.gate([], SHA, {'opus'}, 1), [])

    def test_gate_reports_tier_gap(self):
        lines = ['CLEAR %s model=opus' % SHA, 'CLEAR %s model=sonnet' % SHA]
        gaps = rl.gate(lines, SHA, {'opus', 'gpt-6.1-sol/medium'}, 2)
        self.assertEqual(len(gaps), 1)
        self.assertIn('sonnet', gaps[0])

    def test_gate_ignores_other_sha(self):
        self.assertTrue(rl.gate(['CLEAR %s model=opus' % ('b' * 40)], SHA, {'opus'}, 1))

    def test_gate_ignores_stamp_without_model(self):
        self.assertTrue(rl.gate(['CLEAR %s' % SHA], SHA, {'opus'}, 1))

    def test_not_clear_is_not_a_stamp(self):
        self.assertTrue(rl.gate(['NOT CLEAR %s model=opus' % SHA], SHA, {'opus'}, 1))

    def test_not_clear_not_counted_toward_required(self):
        lines = ['CLEAR %s model=opus' % SHA, 'NOT CLEAR %s model=sonnet' % SHA]
        self.assertTrue(any('found 1' in g for g in rl.gate(lines, SHA, {'opus', 'sonnet'}, 2)))

    def test_not_clear_on_sha_blocks(self):
        lines = ['CLEAR %s model=opus' % SHA, 'NOT CLEAR %s model=gpt-6.1-sol/medium' % SHA]
        self.assertTrue(rl.gate(lines, SHA, {'opus', 'gpt-6.1-sol/medium'}, 1))

    def test_not_clear_other_sha_does_not_block(self):
        lines = ['CLEAR %s model=opus' % SHA, 'NOT CLEAR %s model=opus' % ('b' * 40)]
        self.assertEqual(rl.gate(lines, SHA, {'opus'}, 1), [])

    def test_duplicate_clear_counts_once(self):
        line = 'CLEAR %s model=opus' % SHA
        self.assertTrue(rl.gate([line, line], SHA, {'opus'}, 2))

    def test_tier_removal_rejects_model(self):
        lines = ['CLEAR %s model=sonnet' % SHA]
        self.assertEqual(rl.gate(lines, SHA, {'opus', 'sonnet'}, 1), [])
        self.assertTrue(rl.gate(lines, SHA, {'opus'}, 1))

    def test_string_tier_is_not_substring_matched(self):
        self.assertTrue(rl.gate(['CLEAR %s model=opu' % SHA], SHA, 'opus', 1))
        self.assertEqual(rl.gate(['CLEAR %s model=opus' % SHA], SHA, 'opus', 1), [])

    def test_empty_model_is_not_a_stamp(self):
        self.assertTrue(rl.gate(['CLEAR %s model=' % SHA], SHA, {'opus', ''}, 1))

    def test_exemption_tier_accepts_sonnet(self):
        lines = ['CLEAR %s model=opus' % SHA, 'CLEAR %s model=sonnet' % SHA]
        self.assertEqual(rl.gate(lines, SHA, {'opus', 'sonnet'}, 2), [])

    def test_malformed_not_clear_blocks(self):
        ok = 'CLEAR %s model=opus' % SHA
        for bad in ('NOT CLEAR %s' % SHA, 'NOT CLEAR %s model=opus ' % SHA,
                    'NOT CLEAR %s model=opus\n' % SHA, 'not clear %s model=opus' % SHA,
                    'NOT  CLEAR %s model=opus' % SHA, 'NOT CLEAR %s model=model=x' % SHA,
                    'NOT CLEAR %s model=opus' % SHA.upper()):
            gaps = rl.gate([ok, bad], SHA, {'opus'}, 1)
            self.assertTrue(any('NOT CLEAR' in g for g in gaps), bad)

    def test_other_unparsable_line_is_gap(self):
        for bad in ('CLEAR %s' % SHA, 'CLEAR %s model=opus ' % SHA,
                    'CLEAR %s model=opus' % SHA.upper(), 'CLEAR %s model=model=opus' % SHA):
            gaps = rl.gate(['CLEAR %s model=opus' % SHA, bad], SHA, {'opus'}, 1)
            self.assertTrue(any('unparsable' in g for g in gaps), bad)

    def test_required_validated(self):
        for bad in (0, -1, True, 1.0, '1', None):
            with self.assertRaises(ValueError):
                rl.gate([], SHA, {'opus'}, bad)

    def test_canonical_token(self):
        self.assertEqual(rl.canonical('claude-opus-5-5'), 'opus')
        self.assertEqual(rl.canonical('claude-sonnet-5-5'), 'sonnet')
        self.assertEqual(rl.canonical('gpt-6.1-sol/medium'), 'gpt-6.1-sol/medium')
        self.assertEqual(rl.canonical('opusx'), 'opusx')
        self.assertEqual(rl.gate(['CLEAR %s model=claude-opus-5-5' % SHA], SHA, {'opus'}, 1), [])
        self.assertTrue(rl.gate(['CLEAR %s model=claude-sonnet-5-5' % SHA], SHA, {'opus'}, 1))

    def test_semicolon_not_in_model(self):
        self.assertIsNone(rl.parse('CLEAR %s model=opus;x' % SHA))

    def test_evidence_roundtrip(self):
        lines = ['CLEAR %s model=opus' % SHA, 'NOT CLEAR %s model=opus' % SHA]
        self.assertEqual(rl.split_evidence(rl.join_evidence(lines)), lines)
        self.assertEqual(rl.split_evidence(''), [])


if __name__ == '__main__':
    unittest.main()
