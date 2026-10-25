import json
from pathlib import Path
import pytest
from PIL import Image, PngImagePlugin
from dream import export_artwork, records, build, due_key, validate_data, visibility

@pytest.fixture
def art(tmp_path):
    repo = tmp_path / 'repo'; repo.mkdir()
    source = tmp_path / 'source.png'
    info = PngImagePlugin.PngInfo(); info.add_text('prompt', 'PRIVATE HYPOTHESIS')
    Image.new('RGB', (32, 18), 'blue').save(source, pnginfo=info)
    metadata = tmp_path / 'public.json'
    data = {'id':'test-art', 'title':'Test <art>', 'date':'2026-10-24', 'kind':'test',
            'research':{'summary':'Conceptual art.', 'sources':[]}}
    metadata.write_text(json.dumps(data))
    return repo, source, metadata, data

def test_export_strips_metadata_and_build_is_deterministic(art):
    repo, source, meta, data = art
    export_artwork(repo, source, meta, True)
    assert len(records(repo)) == 1
    assert Image.open(repo / 'gallery/works/test-art/artwork.png').info == {}
    first = build(repo)
    files = {str(p.relative_to(repo / '_site')):p.read_bytes() for p in (repo / '_site').rglob('*') if p.is_file()}
    assert build(repo) == first
    assert files == {str(p.relative_to(repo / '_site')):p.read_bytes() for p in (repo / '_site').rglob('*') if p.is_file()}
    assert 'Test &lt;art&gt;' in (repo / '_site/index.html').read_text()

def test_public_schema_rejects_private_fields_and_paths(art):
    _, _, _, data = art
    data['prompt'] = 'private'
    with pytest.raises(Exception): validate_data(data, 'metadata.schema.json')
    del data['prompt']; data['research']['summary'] = '/Volumes/private'
    with pytest.raises(ValueError): validate_data(data, 'metadata.schema.json')

def test_no_silent_replacement_and_tampering_rejected(art):
    repo, source, meta, _ = art
    export_artwork(repo, source, meta, True)
    export_artwork(repo, source, meta, True)
    Image.new('RGB', (32,18), 'red').save(source)
    with pytest.raises(ValueError): export_artwork(repo, source, meta, True)
    (repo / 'gallery/works/test-art/artwork.png').write_bytes(source.read_bytes())
    with pytest.raises(ValueError): records(repo)

def test_extra_file_or_symlink_blocks_publish(art):
    repo, source, meta, _ = art
    export_artwork(repo, source, meta, True)
    secret = repo / 'gallery/works/test-art/brief.md'; secret.write_text('private')
    with pytest.raises(ValueError): records(repo)
    secret.unlink()
    image = repo / 'gallery/works/test-art/artwork.png'; image.unlink(); image.symlink_to(source)
    with pytest.raises(ValueError): records(repo)

def test_export_requires_review(art):
    with pytest.raises(ValueError): export_artwork(*art[:3])

def test_latest_due_uses_local_time_and_no_backlog():
    assert due_key('America/Los_Angeles','2026-10-24T01:59:00-07:00') == 'nightly-2026-10-23'
    assert due_key('America/Los_Angeles','2026-10-24T02:00:00-07:00') == 'nightly-2026-10-24'
    assert due_key('America/Los_Angeles','2026-11-01T01:30:00-08:00') == 'nightly-2026-10-31'
    with pytest.raises(ValueError): due_key('America/Los_Angeles','2026-10-24T02:00:00')


def test_hidden_art_stays_archived_and_is_not_built(art):
    repo, source, meta, _ = art
    export_artwork(repo, source, meta, True)
    visibility(repo, ['test-art'], False)
    assert build(repo)['count'] == 0
    assert not (repo / '_site/works/test-art').exists()
    assert len(records(repo)) == 1
    # Re-import must not accidentally undo the user's curation.
    export_artwork(repo, source, meta, True)
    assert records(repo)[0]['display'] is False
    visibility(repo, ['test-art'], True)
    assert build(repo)['count'] == 1


def test_public_gallery_has_no_private_feedback_channel(art):
    repo, source, meta, _ = art
    export_artwork(repo, source, meta, True)
    # Private response state is never copied into the public build.
    (repo / 'private-response.json').write_text('{"appeal":"like"}')
    build(repo)
    page = (repo / '_site/index.html').read_text()
    assert '<form' not in page and '<script' not in page
    assert not (repo / '_site/private-response.json').exists()
    (repo / 'site.json').write_text(json.dumps({'feedback_url': 'https://old.example'}))
    with pytest.raises(ValueError):
        build(repo)


def test_legacy_build_marker_is_accepted_during_rename(art):
    repo, source, meta, _ = art
    export_artwork(repo, source, meta, True)
    (repo / '_site').mkdir()
    (repo / '_site/.image-dream-build').write_text('old build')
    assert build(repo)['count'] == 1
    assert (repo / '_site/.nightwork-build').exists()


def test_gallery_identity_is_independent_and_escaped(art):
    repo, source, meta, _ = art
    export_artwork(repo, source, meta, True)
    (repo / 'site.json').write_text(json.dumps({
        'gallery_title': 'Another Look',
        'gallery_intro': 'A <fresh> look & another perspective.',
    }))
    build(repo)
    page = (repo / '_site/index.html').read_text()
    assert '<title>Another Look</title>' in page
    assert '<h1>Another Look</h1>' in page
    assert 'A &lt;fresh&gt; look &amp; another perspective.' in page
    assert 'Built with <a href="https://github.com/ifanirene/nightwork">Nightwork' in page
    (repo / 'site.json').write_text(json.dumps({'gallery_intro': None}))
    with pytest.raises(ValueError, match='gallery_intro must be nonempty text'):
        build(repo)
