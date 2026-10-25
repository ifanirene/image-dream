import json
from unittest.mock import patch
from sources import files, zotero


def test_folder_stays_live_and_does_not_copy_or_follow_external_links(tmp_path):
    root = tmp_path / 'papers'; root.mkdir()
    (root / 'one.pdf').write_bytes(b'first')
    outside = tmp_path / 'private.pdf'; outside.write_bytes(b'private')
    (root / 'link.pdf').symlink_to(outside)
    initial = files(root)
    assert [i['path'] for i in initial['items']] == [str(root / 'one.pdf')]
    assert initial['skipped']
    (root / 'one.pdf').unlink()
    (root / 'two.pdf').write_bytes(b'second')
    assert [i['path'] for i in files(root)['items']] == [str(root / 'two.pdf')]
    assert set(p.name for p in root.iterdir()) == {'two.pdf', 'link.pdf'}


def test_endnote_package_reads_existing_attachments_only(tmp_path):
    package = tmp_path / 'Research.enlp'; package.mkdir()
    library = package / 'Research.enl'; library.write_bytes(b'native-db')
    pdfs = package / 'Research.Data/PDF/123'; pdfs.mkdir(parents=True)
    (pdfs / 'paper.pdf').write_bytes(b'paper')
    result = files(package)
    assert result['kind'] == 'endnote-attachments'
    assert len(result['items']) == 1
    assert files(library)['items'] == result['items']
    assert library.read_bytes() == b'native-db'
    assert 'externally linked' in result['coverage']


def test_zotero_reads_current_collection_and_reports_truncation():
    class Response:
        headers = {'Total-Results': '3'}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return json.dumps([{'key': 'ITEM0001'}, {'key': 'ITEM0002'}]).encode()
    with patch('sources.urlopen', return_value=Response()) as fetch:
        result = zotero(collection='COLL0001', limit=2)
        request = fetch.call_args.args[0]
        assert request.get_method() == 'GET'
        assert '/collections/COLL0001/items/top' in request.full_url
        assert 'limit=2' in request.full_url
        assert result['truncated'] is True


def test_empty_endnote_attachments_are_not_full_library_success(tmp_path):
    library = tmp_path / 'Empty.enl'; library.write_bytes(b'db')
    result = files(library)
    assert not result['items']
    assert result['skipped']
