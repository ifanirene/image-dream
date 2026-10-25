#!/usr/bin/env python3
"""Save explicit in-chat choices beside a private run and summarize personal responses."""
from __future__ import annotations

import argparse
from collections import Counter
import fcntl
import json
from pathlib import Path
import tempfile

from dream_runs import location, now

CHOICES = {'appeal': ('like', 'neutral', 'dislike'), 'association': ('yes', 'not-yet')}


def completed_run(output: Path, key: str) -> Path:
    run = location(output, key)
    state = json.loads((run / 'run.json').read_text())
    if state.get('key') != key or state.get('status') != 'complete':
        raise ValueError('Feedback must refer to the matching completed run')
    return run


def read_response(run: Path, key: str) -> dict:
    path = run / 'feedback.json'
    if not path.exists():
        return {'schema_version': 1, 'key': key, 'appeal': None, 'association': None}
    if path.is_symlink():
        raise ValueError('Feedback must be a regular private file')
    data = json.loads(path.read_text())
    if data.get('schema_version') != 1 or data.get('key') != key:
        raise ValueError('Feedback belongs to a different run or schema')
    for field, choices in CHOICES.items():
        if data.get(field) is not None and data[field] not in choices:
            raise ValueError(f'Invalid stored {field}')
    return data


def record(output: Path, key: str, response_ref: str, appeal: str | None = None,
           association: str | None = None) -> dict:
    updates = {'appeal': appeal, 'association': association}
    if all(value is None for value in updates.values()):
        raise ValueError('Supply at least one explicit choice')
    if not response_ref.strip():
        raise ValueError('Identify the actual user reply, not an inferred preference')
    for field, value in updates.items():
        if value is not None and value not in (*CHOICES[field], 'unanswered'):
            raise ValueError(f'Invalid {field}')
    run = completed_run(output, key)
    with (run / '.feedback.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = read_response(run, key)
        data.setdefault('created_at', now())
        data.setdefault('answer_refs', {})
        for field, value in updates.items():
            if value is not None:
                data[field] = None if value == 'unanswered' else value
                data['answer_refs'][field] = response_ref.strip()
        data['updated_at'] = now()
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=run, delete=False) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
            pending = Path(f.name)
        try:
            pending.replace(run / 'feedback.json')
        finally:
            pending.unlink(missing_ok=True)
    return data


def stats(output: Path) -> dict:
    rows = []
    for path in sorted((output.resolve() / 'runs').glob('*/run.json')):
        state = json.loads(path.read_text())
        if state.get('status') != 'complete':
            continue
        key = state['key']
        if completed_run(output, key) != path.parent:
            raise ValueError('Run directory does not match its key')
        rows.append(read_response(path.parent, key))
    result = {'unit': 'one current personal response per completed local run',
              'completed_runs': len(rows),
              'runs_with_response': sum(any(row[f] is not None for f in CHOICES) for row in rows),
              'dimensions': {}}
    for field, choices in CHOICES.items():
        counts = Counter(row[field] for row in rows if row[field] is not None)
        answered = sum(counts.values())
        result['dimensions'][field] = {
            'answered': answered, 'unanswered': len(rows) - answered,
            'counts': {value: counts[value] for value in choices},
            'percent_of_answers': {value: round(100 * counts[value] / answered, 1) if answered else None
                                   for value in choices},
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('record', 'stats'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--output', type=Path, required=True)
        if name == 'record':
            cmd.add_argument('--key', required=True)
            cmd.add_argument('--response-ref', required=True, help='Private reference to the user reply')
            for field, choices in CHOICES.items():
                cmd.add_argument('--' + field, choices=(*choices, 'unanswered'))
    args = vars(parser.parse_args())
    command = args.pop('command')
    try:
        result = globals()[command](**args)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(1, f'{exc}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
