"""Pinned offline task data and descriptive fixed-reference scoring (no executor)."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'evaluation-fixtures'
TASKS = ('shared-adapter', 'path-symlink')
FILES = {task + suffix for task in TASKS
         for suffix in ('.json', '-broken.go', '-correct.go')}


class FixtureError(ValueError):
    pass


def canonical(record):
    return (json.dumps(record, indent=2) + '\n').encode('utf-8')


def pins():
    result = json.loads((ROOT / 'pins.json').read_text())
    if set(result) != FILES:
        raise FixtureError('fixture pin inventory mismatch')
    return result


def verify_record(task, record):
    if task not in TASKS:
        raise FixtureError('unknown task: ' + task)
    if hashlib.sha256(canonical(record)).hexdigest() != pins()[task + '.json']:
        raise FixtureError('fixture pin mismatch: ' + task)


def load_fixtures():
    expected = pins()
    for name, digest in expected.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise FixtureError('fixture pin mismatch: ' + name)
    records = {task: json.loads((ROOT / (task + '.json')).read_text()) for task in TASKS}
    for task, record in records.items():
        verify_record(task, record)
    return records


def score(task, observations):
    """Score supplied observable values; never execute candidate code."""
    records = load_fixtures()
    if task not in records:
        raise FixtureError('unknown task: ' + task)
    cases = records[task]['cases']
    if not isinstance(observations, dict) or set(observations) - {c['id'] for c in cases}:
        raise FixtureError('unexpected observation')
    failures, unknown, details = [], [], []
    passed = 0
    for case in cases:
        name = case['id']
        actual = observations.get(name)
        if actual is None:
            unknown.append(name)
            details.append({'criterion': name, 'status': 'unknown',
                            'reason': 'observation absent or null'})
        elif type(actual) is type(case['expected']) and actual == case['expected']:
            passed += 1
            details.append({'criterion': name, 'status': 'pass'})
        else:
            failures.append(name)
            details.append({'criterion': name, 'status': 'fail',
                            'expected': case['expected'], 'observed': actual})
    return {'passed': passed, 'failures': failures, 'unknown': unknown,
            'complete': not failures and not unknown, 'criteria': details,
            'policy_violations': None, 'review_findings': None,
            'human_review_seconds': None,
            'efficiency': {'billed_cost_usd': None, 'input_tokens': None,
                           'output_tokens': None, 'reasoning_tokens': None,
                           'latency_ms': None, 'execution_time_ms': None}}


def reference(task, variant, inputs):
    """Two fixed local demonstrations, not a submitted-program evaluator."""
    if task not in TASKS or variant not in ('broken', 'correct'):
        raise FixtureError('unknown fixed reference')
    if task == 'shared-adapter':
        if variant == 'broken':
            return inputs['name']
        return 'DENIED' if inputs['denied'] else inputs['name'].strip()
    name = inputs['name']
    if variant == 'broken':
        return bool(name)
    if not name or name.startswith('/'):
        return False
    components = []
    for part in name.split('/'):
        if part == '..':
            return False
        if part in ('', '.'):
            continue
        components.append(part)
        if '/'.join(components) in inputs['symlinks']:
            return False
    return bool(components)


def self_check():
    records = load_fixtures()
    tasks = {}
    for task, record in records.items():
        tasks[task] = {variant: score(task, {
            case['id']: reference(task, variant, case['input']) for case in record['cases']})
            for variant in ('broken', 'correct')}
        if tasks[task]['broken']['complete'] or not tasks[task]['correct']['complete']:
            raise FixtureError('fixed-reference demonstration failed: ' + task)
    return {'version': 1, 'synthetic': True,
            'execution': 'fixed Python reference replays; Go sources are data',
            'fixture_sha256': {task: pins()[task + '.json'] for task in TASKS},
            'source_sha256': pins(), 'tasks': tasks,
            'limitations': ['No target Go execution, model runs or runtime enforcement measured.',
                            'Independent review and live scoring calibration remain required.',
                            'Static symlink cases do not establish race-safe file access.',
                            'No causal effectiveness or adoption conclusion.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        report = self_check()
    except (FixtureError, OSError, ValueError) as exc:
        print('evaluation fixtures: ' + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
