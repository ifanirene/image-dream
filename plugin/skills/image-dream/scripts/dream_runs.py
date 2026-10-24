#!/usr/bin/env python3
"""Reserve scheduled occurrences and record local Image Dream outcomes. No network calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def location(output: Path, key: str) -> Path:
    if not key.strip():
        raise ValueError('Occurrence key must not be empty')
    # Keys may contain timezone offsets or arbitrary labels, never path components.
    return output.resolve() / 'runs' / hashlib.sha256(key.encode()).hexdigest()[:24]


def reserve(output: Path, key: str) -> dict:
    run = location(output, key)
    run.parent.mkdir(parents=True, exist_ok=True)
    try:
        run.mkdir()
    except FileExistsError:
        record = run / 'run.json'
        state = json.loads(record.read_text()) if record.is_file() else {'status': 'interrupted'}
        return {'claimed': False, 'directory': str(run), 'record': state}
    state = {'key': key, 'status': 'reserved', 'created_at': now()}
    pending = run / 'reserve.pending.json'
    pending.write_text(json.dumps(state, indent=2) + '\n')
    pending.replace(run / 'run.json')
    return {'claimed': True, 'directory': str(run), 'record': state}


def artifact(path: Path | None, run: Path, name: str) -> str:
    if path is None:
        raise ValueError(f'{name} is required for completion')
    real = path.resolve()
    if not real.is_relative_to(run) or not real.is_file() or real.stat().st_size == 0:
        raise ValueError(f'{name} must be a nonempty file inside this run directory')
    return str(real.relative_to(run))


def finish(output: Path, key: str, status: str, note: str, image: Path | None = None,
           prompt: Path | None = None, brief: Path | None = None) -> dict:
    run = location(output, key)
    record = run / 'run.json'
    state = json.loads(record.read_text())
    if state.get('key') != key or state.get('status') != 'reserved':
        raise ValueError('Only the matching reserved occurrence can be finished')
    if status not in {'complete', 'failed', 'blocked'} or not note.strip():
        raise ValueError('Use complete, failed, or blocked with a nonempty outcome note')
    fields = {}
    if status == 'complete':
        fields = {name: artifact(value, run, name)
                  for name, value in [('image', image), ('prompt', prompt), ('brief', brief)]}
        # Check common raster signatures, not filenames; agent still performs visual QA.
        with (run / fields['image']).open('rb') as stream:
            header = stream.read(12)
        raster = (header.startswith(b'\x89PNG\r\n\x1a\n') or header.startswith(b'\xff\xd8\xff')
                  or (header.startswith(b'RIFF') and header[8:12] == b'WEBP')
                  or header.startswith((b'GIF87a', b'GIF89a')))
        if not raster:
            raise ValueError('Image does not have a supported PNG/JPEG/WebP/GIF signature')
    state.update(status=status, finished_at=now(), note=note, **fields)
    # Single-writer marker also preserves evidence if finalization was interrupted.
    marker = run / '.finish-claimed'
    try:
        with marker.open('x') as stream:
            stream.write(now())
    except FileExistsError as exc:
        raise ValueError('Finalization already claimed; inspect existing files before recovery') from exc
    pending = run / 'run.pending.json'
    pending.write_text(json.dumps(state, indent=2) + '\n')
    pending.replace(record)
    return {'directory': str(run), 'record': state}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('reserve', 'finish'):
        sub = commands.add_parser(name)
        sub.add_argument('--output', type=Path, required=True)
        sub.add_argument('--key', required=True)
        if name == 'finish':
            sub.add_argument('--status', choices=['complete', 'failed', 'blocked'], required=True)
            sub.add_argument('--note', required=True)
            for value in ('image', 'prompt', 'brief'):
                sub.add_argument('--' + value, type=Path)
    args = vars(parser.parse_args())
    command = args.pop('command')
    try:
        result = reserve(**args) if command == 'reserve' else finish(**args)
    except (OSError, ValueError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
