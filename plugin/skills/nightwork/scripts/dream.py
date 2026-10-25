#!/usr/bin/env python3
"""Nightwork: private run bookkeeping, explicit public export, static gallery and Git push."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.request import urlopen
from zoneinfo import ZoneInfo

from PIL import Image, ImageOps
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from jsonschema import Draft202012Validator, FormatChecker
import dream_runs

SKILL = Path(__file__).resolve().parents[1]
ASSETS = SKILL / 'assets'
ID = re.compile(r'^[a-z0-9][a-z0-9-]{0,95}$')


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write('\n')
        temp = Path(f.name)
    temp.replace(path)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_data(data: dict, schema_name: str = 'record.schema.json') -> None:
    schema = read_json(ASSETS / schema_name)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(data)
    # Structural checks do not replace the agent's review of scientific meaning/privacy.
    text = json.dumps(data, ensure_ascii=False)
    for forbidden in ('/Users/', '/Volumes/', 'file://', 'libfile_', 'chatgpt.com/c/', 'sk-proj-'):
        if forbidden in text:
            raise ValueError(f'Private identifier/path in public record: {forbidden}')
    for source in data['research']['sources']:
        url = urlsplit(source['url'])
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValueError('Research links must be public HTTPS URLs without credentials')
        if url.hostname in {'localhost', '127.0.0.1'} or url.query:
            raise ValueError('Use stable public research URLs without query tokens')


def clean_pixels(path: Path) -> Image.Image:
    with Image.open(path) as src:
        src.load()
        if getattr(src, 'n_frames', 1) != 1:
            raise ValueError('Only still images are supported; preserve animations privately')
        oriented = ImageOps.exif_transpose(src)
        mode = 'RGBA' if 'A' in oriented.getbands() else 'RGB'
        # A fresh image strips embedded prompts, EXIF and other private metadata.
        pixels = Image.new(mode, oriented.size)
        pixels.paste(oriented.convert(mode))
        return pixels


def export_artwork(repo: Path, image: Path, metadata: Path, reviewed: bool = False) -> dict:
    if not reviewed:
        raise ValueError('Inspect the actual image and public text before using --reviewed')
    data = read_json(metadata)
    validate_data(data, 'metadata.schema.json')
    root = repo.resolve() / 'gallery' / 'works'
    root.mkdir(parents=True, exist_ok=True)
    target = root / data['id']
    if target.is_symlink():
        raise ValueError('Artwork directory cannot be a symlink')
    with tempfile.TemporaryDirectory(dir=root, prefix='.export-') as tmp:
        tmp = Path(tmp)
        pixels = clean_pixels(image)
        pixels.save(tmp / 'artwork.png', format='PNG', compress_level=6)
        record = {**data, 'schema_version': 1, 'ai_generated': True,
                  'image': {'file': 'artwork.png', 'width': pixels.width, 'height': pixels.height,
                            'sha256': sha(tmp / 'artwork.png')}}
        validate_data(record)
        # Same occurrence must not silently acquire a different image.
        if target.exists():
            old = read_json(target / 'record.json')
            if old['image']['sha256'] != record['image']['sha256']:
                raise ValueError('Existing artwork differs; use a new linked artwork ID')
            if 'display' not in data and 'display' in old:
                record['display'] = old['display']
            write_json(target / 'record.json', record)
        else:
            write_json(tmp / 'record.json', record)
            target.mkdir()
            try:
                shutil.copy2(tmp / 'artwork.png', target / 'artwork.png')
                shutil.copy2(tmp / 'record.json', target / 'record.json')
            except BaseException:
                # Leave interrupted output visible to validation; do not silently publish it.
                raise
    return {'id': data['id'], 'status': 'exported', 'sha256': record['image']['sha256']}


def records(repo: Path) -> list[dict]:
    root = repo.resolve() / 'gallery' / 'works'
    if not root.is_dir():
        raise ValueError('Missing gallery/works')
    out, hashes = [], set()
    for folder in sorted(root.iterdir()):
        if folder.name.startswith('.'):
            raise ValueError(f'Unexpected temporary/hidden gallery entry: {folder.name}')
        if not folder.is_dir() or folder.is_symlink() or not ID.fullmatch(folder.name):
            raise ValueError(f'Invalid artwork directory: {folder.name}')
        if {p.name for p in folder.iterdir()} != {'record.json', 'artwork.png'}:
            raise ValueError(f'Unexpected or missing files in artwork {folder.name}')
        if any(p.is_symlink() for p in folder.iterdir()):
            raise ValueError('Symlinks are not public assets')
        record = read_json(folder / 'record.json')
        validate_data(record)
        if record['id'] != folder.name:
            raise ValueError('Artwork ID does not match its directory')
        path = folder / 'artwork.png'
        if sha(path) != record['image']['sha256']:
            raise ValueError(f'Image hash mismatch: {folder.name}')
        with Image.open(path) as img:
            img.load()
            if img.format != 'PNG' or img.size != (record['image']['width'], record['image']['height']):
                raise ValueError(f'Invalid image format or dimensions: {folder.name}')
            if img.info:
                raise ValueError(f'Unexpected embedded image metadata: {folder.name}')
            pixel_hash = hashlib.sha256(img.convert('RGBA').tobytes()).hexdigest()
        if pixel_hash in hashes:
            raise ValueError(f'Duplicate image pixels: {folder.name}; reconcile aliases privately')
        hashes.add(pixel_hash)
        out.append(record)
    return sorted(out, key=lambda r: (r['date'] or '', r['id']), reverse=True)


def visibility(repo: Path, ids: list[str], visible: bool) -> dict:
    existing = {r['id']: r for r in records(repo)}
    if any(work_id not in existing for work_id in ids):
        raise ValueError('Unknown artwork ID; nothing changed')
    for work_id in ids:
        record = existing[work_id]
        record['display'] = visible
        write_json(repo / 'gallery' / 'works' / work_id / 'record.json', record)
    return {'display': visible, 'ids': ids}


def revision(repo: Path) -> str:
    try:
        return subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return 'uncommitted'


def site_settings(repo: Path) -> dict:
    settings = {
        'github_url': 'https://github.com/ifanirene/nightwork',
        'gallery_title': 'Nightwork',
        'gallery_intro': 'Artworks and short notes sparked by working research libraries.',
    }
    path = repo / 'site.json'
    if path.exists():
        data = read_json(path)
        if set(data) - {'github_url', 'gallery_url', 'gallery_title', 'gallery_intro'}:
            raise ValueError('Unknown public site setting')
        settings.update(data)
    for field in ('github_url', 'gallery_url'):
        value = settings.get(field)
        if value is not None:
            url = urlsplit(value)
            if url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment:
                raise ValueError(f'{field} must be a public HTTPS URL without credentials or query parameters')
    for field in ('gallery_title', 'gallery_intro'):
        if not isinstance(settings[field], str) or not settings[field].strip():
            raise ValueError(f'{field} must be nonempty text')
    return settings


def build(repo: Path) -> dict:
    repo = repo.resolve()
    works = [r for r in records(repo) if r.get('display', True)]
    settings = site_settings(repo)
    output = repo / '_site'
    if output.is_symlink():
        raise ValueError('_site must not be a symlink')
    if output.exists():
        if not any((output / marker).is_file() for marker in ('.nightwork-build', '.image-dream-build')):
            raise ValueError('Refusing to replace unrecognized _site directory')
        shutil.rmtree(output)
    output.mkdir()
    (output / '.nightwork-build').write_text('Generated by Nightwork\n')
    (output / '.nojekyll').touch()
    env = Environment(loader=FileSystemLoader(ASSETS), autoescape=select_autoescape(['html']),
                      undefined=StrictUndefined)
    for record in works:
        dest = output / 'works' / record['id']
        dest.mkdir(parents=True)
        source = repo / 'gallery' / 'works' / record['id']
        shutil.copy2(source / 'artwork.png', dest / 'artwork.png')
        shutil.copy2(source / 'record.json', dest / 'record.json')
        with Image.open(source / 'artwork.png') as img:
            img.thumbnail((960, 960), Image.Resampling.LANCZOS)
            img.save(dest / 'preview.webp', format='WEBP', quality=85, method=6)
    digest = hashlib.sha256(json.dumps(works, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    manifest = {'schema_version': 1, 'revision': revision(repo), 'records_sha256': digest,
                'count': len(works), 'ids': [r['id'] for r in works]}
    write_json(output / 'site-manifest.json', manifest)
    (output / 'index.html').write_text(env.get_template('index.html').render(works=works, **settings), encoding='utf-8')
    shutil.copy2(ASSETS / 'style.css', output / 'style.css')
    return manifest


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


@contextmanager
def publish_lock(repo: Path):
    gitdir = Path(git(repo, 'rev-parse', '--absolute-git-dir'))
    with (gitdir / 'image-dream-publish.lock').open('w') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def publish(repo: Path, branch: str = 'main') -> dict:
    repo = repo.resolve()
    with publish_lock(repo):
        if git(repo, 'branch', '--show-current') != branch:
            raise ValueError(f'Expected existing {branch} branch; will not switch branches')
        if git(repo, 'diff', '--cached', '--name-only'):
            raise ValueError('Index already has staged changes; review them separately')
        build(repo)
        # Explicitly stage gallery files only. Never git add . or force-push.
        changes = git(repo, 'status', '--porcelain', '--untracked-files=all', '--', 'gallery/works')
        if changes:
            git(repo, 'add', '--', 'gallery/works')
            staged = git(repo, 'diff', '--cached', '--name-only').splitlines()
            allowed = re.compile(r'^gallery/works/[a-z0-9-]+/(record\.json|artwork\.png)$')
            if not all(allowed.fullmatch(p) for p in staged):
                raise ValueError('Unexpected staged file; no commit or push was performed')
            git(repo, 'commit', '-m', 'art: update Nightwork gallery')
        git(repo, 'push', 'origin', branch)
        return {'status': 'pushed', 'revision': revision(repo),
                'note': 'Pages deployment is separate; verify its run and online manifest.'}


def verify_site(url: str, expected_revision: str) -> dict:
    if not url.startswith('https://'):
        raise ValueError('Expected an HTTPS gallery URL')
    with urlopen(url.rstrip('/') + '/site-manifest.json', timeout=30) as response:
        manifest = json.load(response)
    if manifest['revision'] != expected_revision:
        raise ValueError('Online gallery still serves a different revision')
    with urlopen(url, timeout=30) as response:
        page = response.read().decode('utf-8')
    for work_id in manifest['ids']:
        if not ID.fullmatch(work_id) or f'id="{work_id}"' not in page:
            raise ValueError('Online page and manifest disagree')
    return {'status': 'deployed', **manifest, 'url': url}


def due_key(timezone: str, at: str | None) -> str:
    date = datetime.fromisoformat(at) if at else datetime.now(ZoneInfo(timezone))
    if date.tzinfo is None:
        raise ValueError('--at requires a timezone offset')
    date = date.astimezone(ZoneInfo(timezone))
    if date.hour < 2:
        date -= timedelta(days=1)
    return 'nightly-' + date.date().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'build', 'publish'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--repo', type=Path, required=True)
        if name == 'publish':
            cmd.add_argument('--branch', default='main')
    for name in ('hide', 'show'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--repo', type=Path, required=True)
        cmd.add_argument('--ids', nargs='+', required=True)
    cmd = sub.add_parser('export')
    cmd.add_argument('--repo', type=Path, required=True)
    cmd.add_argument('--image', type=Path, required=True)
    cmd.add_argument('--metadata', type=Path, required=True)
    cmd.add_argument('--reviewed', action='store_true')
    cmd = sub.add_parser('verify')
    cmd.add_argument('--url', required=True)
    cmd.add_argument('--revision', required=True)
    cmd = sub.add_parser('due')
    cmd.add_argument('--timezone', default='America/Los_Angeles')
    cmd.add_argument('--at')
    args = vars(parser.parse_args())
    command = args.pop('command')
    try:
        if command in ('hide', 'show'):
            result = visibility(**args, visible=command == 'show')
        elif command == 'validate':
            result = {'valid': True, 'count': len(records(**args))}
        elif command == 'export':
            result = export_artwork(**args)
        elif command == 'verify':
            result = verify_site(args['url'], args['revision'])
        elif command == 'due':
            result = {'key': due_key(**args)}
        else:
            result = globals()[command](**args)
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({'error': str(exc), 'step': command}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
