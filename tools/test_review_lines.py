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

    def test_review_started_is_not_a_stamp(self):
        self.assertTrue(rl.gate(['review started %s model=opus' % SHA], SHA, {'opus'}, 1))

    def test_distinct_count_uses_canonical_model(self):
        lines = ['CLEAR %s model=opus' % SHA, 'CLEAR %s model=claude-opus-5-5' % SHA]
        gaps = rl.gate(lines, SHA, {'opus'}, 2)
        self.assertTrue(any('found 1' in g for g in gaps))
        self.assertEqual(rl.gate(lines, SHA, {'opus'}, 1), [])
        mixed = ['CLEAR %s model=claude-opus-5-5' % SHA, 'CLEAR %s model=gpt-6.1-sol/medium' % SHA]
        self.assertEqual(rl.gate(mixed, SHA, {'opus', 'gpt-6.1-sol/medium'}, 2), [])

    def test_same_model_twice_counts_once(self):
        lines = ['CLEAR %s model=opus' % SHA, 'CLEAR %s model=opus' % SHA]
        self.assertTrue(rl.gate(lines, SHA, {'opus'}, 2))

    def test_claude_id_needs_version_shape(self):
        for ok, fam in (('claude-opus-5-5', 'opus'), ('claude-sonnet-4', 'sonnet'),
                        ('claude-haiku-4-5-20251001', 'haiku')):
            self.assertEqual(rl.canonical(ok), fam)
        for bad in ('claude-opus-x', 'claude-opus--', 'claude-opus-sonnet-5', 'claude-opusx',
                    'claude-opus-5-5_x', 'xclaude-opus-5', 'claude-opus-5-5-x', 'claude-opus-',
                    'claude-opus-5-5x'):
            self.assertEqual(rl.canonical(bad), bad)

    def test_malformed_not_clear_blocks_unless_foreign_full_sha(self):
        ok = 'CLEAR %s model=opus' % SHA
        other = 'b' * 40
        for bad in ('NOT CLEAR model=claude-opus-5-5-20260101', 'NOT CLEAR model=opus-20260101',
                    'NOT CLEAR 20260101 model=opus', 'NOT CLEAR 1234567890 model=opus',
                    'NOT CLEAR %s model=opus' % SHA[:7], 'NOT CLEAR %s' % SHA[:12],
                    'NOT CLEAR', 'not clear model=opus',
                    'NOT CLEAR model: claude-opus-5-5-20260101', 'NOT\tCLEAR model=opus',
                    'NOT CLEAR (%s) model=opus' % SHA[:8], 'NOT CLEAR (model=opus)',
                    'NOT CLEAR %s model=opus %s' % (other, SHA), 'NOT CLEAR %s %s' % (SHA, other)):
            self.assertTrue(any('NOT CLEAR' in g for g in rl.gate([ok, bad], SHA, {'opus'}, 1)), bad)
        for fine in ('NOT CLEAR %s model=opus ' % other, 'NOT CLEAR (%s) model=opus' % other,
                     'NOT CLEAR %s model: opus' % other):
            self.assertEqual(rl.gate([ok, fine], SHA, {'opus'}, 1), [], fine)

    def test_any_lower_tier_clear_blocks_even_if_extra(self):
        lines = ['CLEAR %s model=opus' % SHA, 'CLEAR %s model=sonnet' % SHA]
        gaps = rl.gate(lines, SHA, {'opus'}, 1)
        self.assertEqual(len(gaps), 1)
        self.assertIn('sonnet', gaps[0])

    def test_tier_gap_message_joins_with_comma(self):
        gaps = rl.gate(['CLEAR %s model=sonnet' % SHA], SHA, {'opus', 'gpt-6.1-sol/medium'}, 1)
        self.assertIn('gpt-6.1-sol/medium, opus', gaps[0])

    def test_sha_inside_model_token_is_gap(self):
        other = 'b' * 40
        gaps = rl.gate(['CLEAR %s model=x%sx' % (other, SHA)], SHA, {'opus'}, 1)
        self.assertTrue(any('inside its model token' in g for g in gaps))

    def test_note_with_several_lines_splits_into_entries(self):
        other = 'b' * 40
        note = ('NOT CLEAR %s role=review model=sonnet\n'
                'CLEAR %s role=review model=claude-opus-5-5\n'
                '\nCLEAR %s role=qa model=opus/high\n' % (SHA, SHA, other))
        lines = rl.split_note(note)
        self.assertEqual(len(lines), 3)
        self.assertEqual(rl.parse(lines[1]), ('CLEAR', SHA, 'claude-opus-5-5'))
        self.assertEqual(rl.parse(lines[2]), ('CLEAR', other, 'opus/high'))
        self.assertIn('NOT CLEAR recorded on %s' % SHA, rl.gate(lines, SHA, {'opus'}, 1))
        self.assertEqual(rl.gate(lines[1:2], SHA, {'opus'}, 1), [])

    def test_role_is_optional_and_validated(self):
        self.assertIsNotNone(rl.parse('CLEAR %s model=opus' % SHA))
        self.assertIsNotNone(rl.parse('CLEAR %s role=qa model=opus' % SHA))
        for bad in ('CLEAR %s role= model=opus' % SHA, 'CLEAR %s role=a role=b model=opus' % SHA,
                    'CLEAR %s role=Review model=opus' % SHA, 'CLEAR %s model=opus role=qa' % SHA):
            self.assertIsNone(rl.parse(bad), bad)


if __name__ == '__main__':
    unittest.main()
