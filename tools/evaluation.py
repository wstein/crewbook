"""Offline validation/reporting of explicitly scored evaluation evidence."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


class EvidenceError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def fields(value, names):
    require(isinstance(value, dict) and set(value) == set(names.split()),
            'expected fields: ' + names)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value)


def integer(value):
    return type(value) is int and value >= 0


def summarize(data):
    fields(data, 'version synthetic configuration tasks arms repetitions runs')
    require(type(data['version']) is int and data['version'] == 1, 'unsupported version')
    require(type(data['synthetic']) is bool, 'synthetic must be boolean')
    config = data['configuration']
    fields(config, 'repository_revision client model reasoning instruction_sha256 environment_sha256')
    require(isinstance(config['repository_revision'], str) and
            re.fullmatch(r'[0-9a-f]{40}', config['repository_revision']), 'invalid repository revision')
    require(all(nonempty(config[k]) for k in ('client', 'model', 'reasoning')), 'missing client binding')
    require(sha(config['environment_sha256']), 'invalid environment fingerprint')
    require(isinstance(config['instruction_sha256'], list) and config['instruction_sha256'] and
            all(sha(v) for v in config['instruction_sha256']), 'invalid instruction hashes')
    require(isinstance(data['tasks'], list) and data['tasks'], 'tasks required')
    tasks = {}
    for task in data['tasks']:
        fields(task, 'id fixture_sha256 criteria')
        require(nonempty(task['id']) and task['id'] not in tasks, 'duplicate/invalid task')
        require(sha(task['fixture_sha256']), 'invalid fixture hash')
        criteria = task['criteria']
        require(isinstance(criteria, list) and criteria and all(nonempty(v) for v in criteria)
                and len(set(criteria)) == len(criteria), 'invalid criteria')
        tasks[task['id']] = criteria
    arms = data['arms']
    require(isinstance(arms, list) and arms and all(nonempty(v) for v in arms)
            and len(set(arms)) == len(arms), 'invalid arms')
    require(type(data['repetitions']) is int and data['repetitions'] > 0, 'invalid repetitions')
    expected = {(t, r, a) for t in tasks for r in range(data['repetitions']) for a in arms}
    require(isinstance(data['runs'], list), 'runs must be a list')
    seen = set()
    counts = {a: {'scored': 0, 'failed': 0, 'missing': 0} for a in arms}
    for run in data['runs']:
        fields(run, 'task repetition arm status configuration outcomes efficiency note')
        require(nonempty(run['task']) and nonempty(run['arm']) and integer(run['repetition']),
                'invalid run identity')
        key = (run['task'], run['repetition'], run['arm'])
        require(key in expected and key not in seen, 'unexpected/duplicate run slot')
        seen.add(key)
        require(run['configuration'] == config, 'unlike configurations cannot be aggregated')
        require(run['status'] in ('scored', 'failed', 'missing'), 'invalid status')
        require(isinstance(run['note'], str), 'note must be text')
        if run['status'] != 'scored':
            require(run['outcomes'] is None and nonempty(run['note']),
                    'failed/missing runs need null outcomes and an explanation')
        else:
            outcomes = run['outcomes']
            fields(outcomes, 'criteria meaningful_checks policy_violations review_findings human_review_seconds')
            require(isinstance(outcomes['criteria'], dict) and
                    set(outcomes['criteria']) == set(tasks[run['task']]) and
                    all(type(v) is bool for v in outcomes['criteria'].values()), 'invalid criterion scores')
            require(type(outcomes['meaningful_checks']) is bool, 'checks must be boolean')
            require(integer(outcomes['policy_violations']) and integer(outcomes['review_findings']),
                    'adverse outcome counts must be nonnegative integers')
            require(outcomes['human_review_seconds'] is None or integer(outcomes['human_review_seconds']),
                    'human effort must be null or nonnegative integer seconds')
        fields(run['efficiency'], 'billed_cost_usd input_tokens output_tokens reasoning_tokens latency_ms retries diff_lines cache_tokens')
        for name, value in run['efficiency'].items():
            if name == 'billed_cost_usd':
                require(value is None or (type(value) in (int, float) and
                        0 <= value < float('inf')), 'invalid billed cost')
            else:
                require(value is None or integer(value), 'invalid efficiency metric: ' + name)
        counts[run['arm']][run['status']] += 1
    require(seen == expected, 'every planned slot must be recorded, including missing runs')
    return {'version': 1, 'synthetic': data['synthetic'], 'configuration': config,
            'sample_sizes': counts, 'runs': data['runs'],
            'limitations': ['Descriptive scored evidence only; no causal or adoption conclusion.',
                            'Hashes and configuration are supplied assertions, not runtime verification.',
                            'Null metrics remain unknown; failed and missing runs are retained.']}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON field: ' + key)
        result[key] = value
    return result


def load(path):
    raw = Path(path).read_bytes()
    data = json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda v: (_ for _ in ()).throw(EvidenceError('invalid constant: ' + v)))
    result = summarize(data)
    result['evidence_sha256'] = hashlib.sha256(raw).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', type=Path)
    args = parser.parse_args()
    try:
        result = load(args.evidence)
    except (EvidenceError, OSError, ValueError) as exc:
        print('evaluation: ' + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
