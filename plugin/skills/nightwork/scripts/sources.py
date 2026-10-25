#!/usr/bin/env python3
"""Inspect existing research sources in place; emit a private, disposable inventory."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

TEXT_TYPES = {'.pdf', '.md', '.txt'}
ZOTERO = 'http://127.0.0.1:23119/api'


def files(path: Path) -> dict:
    path = path.expanduser().resolve(strict=True)
    kind, roots, coverage = 'folder', [path], 'PDF and text files at the selected location'
    if path.suffix.lower() == '.enl' and path.is_file():
        kind, roots = 'endnote-attachments', [path.with_suffix('.Data') / 'PDF']
    elif path.suffix.lower() == '.enlp' and path.is_dir():
        kind = 'endnote-attachments'
        libraries = sorted(path.glob('*.enl'))
        if len(libraries) != 1:
            raise ValueError('Select a package with one .enl file, or its existing PDF folder')
        roots = [libraries[0].with_suffix('.Data') / 'PDF']
    if kind == 'endnote-attachments':
        coverage = ('Existing internal PDF attachments only. EndNote groups, notes, '
                    'records without PDFs and externally linked attachments are not read.')
    items, skipped = [], []
    for root in roots:
        if not root.exists():
            skipped.append(f'No internal attachments at {root}')
            continue
        allowed = {'.pdf'} if kind == 'endnote-attachments' else TEXT_TYPES
        paths = [root] if root.is_file() else sorted(root.rglob('*'))
        for candidate in paths:
            if candidate.suffix.lower() not in allowed or not candidate.is_file():
                continue
            # An inventory of one chosen directory must not follow links out of it.
            if candidate.is_symlink() or not candidate.resolve().is_relative_to(root if root.is_dir() else root.parent):
                skipped.append(f'Symlink outside selected source: {candidate}')
                continue
            stat = candidate.stat()
            items.append({'path': str(candidate), 'format': candidate.suffix[1:].lower(),
                          'bytes': stat.st_size, 'modified_ns': stat.st_mtime_ns})
    return {'source': str(path), 'kind': kind, 'coverage': coverage,
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'items': items, 'skipped': skipped,
            'note': 'Paths and metadata only; no claim that file contents have been read. '
                    'Rerun to see changes. Keep this inventory private.'}


def zotero(collection: str | None = None, item: str | None = None, limit: int = 200) -> dict:
    for key in (collection, item):
        if key and not re.fullmatch(r'[A-Z0-9]{8}', key):
            raise ValueError('Zotero keys must have eight uppercase letters/digits')
    if not 1 <= limit <= 5000:
        raise ValueError('Choose a limit from 1 to 5000')
    route = f'/users/0/items/{item}/children' if item else (
        f'/users/0/collections/{collection}/items/top' if collection else '/users/0/items/top')
    items, total = [], None
    while len(items) < limit:
        query = urlencode({'format': 'json', 'limit': min(100, limit - len(items)), 'start': len(items)})
        request = Request(ZOTERO + route + '?' + query, headers={'Zotero-API-Version': '3'})
        with urlopen(request, timeout=15) as response:
            batch = json.load(response)
            total_header = response.headers.get('Total-Results')
            if total_header:
                total = int(total_header)
        if not isinstance(batch, list):
            raise ValueError('Unexpected response from Zotero')
        items.extend(batch)
        if not batch or (total is not None and len(items) >= total):
            break
    return {'kind': 'zotero-local', 'collection': collection, 'parent_item': item,
            'checked_at': datetime.now(timezone.utc).isoformat(), 'items': items,
            'truncated': len(items) < total if total is not None else len(items) >= limit,
            'note': 'Read from the current Zotero local API; this response is not a second library. '
                    'Metadata and child notes do not establish that an attached paper has been read.'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    cmd = sub.add_parser('files')
    cmd.add_argument('path', type=Path)
    cmd = sub.add_parser('zotero')
    cmd.add_argument('--collection')
    cmd.add_argument('--item', help='Read one selected item’s child notes/attachment metadata')
    cmd.add_argument('--limit', type=int, default=200)
    args = vars(parser.parse_args())
    name = args.pop('command')
    try:
        print(json.dumps(globals()[name](**args), ensure_ascii=False, indent=2))
    except Exception as exc:
        parser.exit(1, f'{exc}\nFor Zotero, open the app and enable local application access in Advanced settings.\n')


if __name__ == '__main__':
    main()
