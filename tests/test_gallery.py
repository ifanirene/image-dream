import json
from pathlib import Path
import pytest
from PIL import Image, PngImagePlugin
from dream import export_artwork, records, build, due_key, validate_data

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
