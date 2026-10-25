import json
import pytest

from dream_runs import reserve, location
from feedback import record, stats


def complete(root, key):
    run = reserve(root, key)
    path = location(root, key) / 'run.json'
    state = run['record']
    state['status'] = 'complete'
    path.write_text(json.dumps(state))


def test_partial_answers_revisions_and_denominators(tmp_path):
    complete(tmp_path, 'one')
    complete(tmp_path, 'two')
    reserve(tmp_path, 'unfinished')
    record(tmp_path, 'one', 'user-reply-1', appeal='like')
    result = stats(tmp_path)
    assert result['completed_runs'] == 2
    assert result['dimensions']['appeal']['answered'] == 1
    assert result['dimensions']['association']['unanswered'] == 2
    assert result['dimensions']['association']['percent_of_answers']['yes'] is None
    record(tmp_path, 'one', 'user-reply-2', association='not-yet')
    changed = record(tmp_path, 'one', 'user-reply-3', appeal='dislike')
    assert changed['association'] == 'not-yet'
    assert changed['answer_refs'] == {'appeal': 'user-reply-3', 'association': 'user-reply-2'}
    record(tmp_path, 'one', 'user-reply-3', appeal='dislike')
    result = stats(tmp_path)
    assert result['runs_with_response'] == 1
    assert result['dimensions']['appeal']['counts'] == {'like': 0, 'neutral': 0, 'dislike': 1}
    assert result['dimensions']['appeal']['percent_of_answers']['dislike'] == 100
    record(tmp_path, 'one', 'user-reply-4', appeal='unanswered', association='unanswered')
    assert stats(tmp_path)['runs_with_response'] == 0


def test_no_phantom_or_inferred_responses(tmp_path):
    with pytest.raises(OSError):
        record(tmp_path, 'missing', 'user-reply', appeal='like')
    reserve(tmp_path, 'reserved')
    with pytest.raises(ValueError):
        record(tmp_path, 'reserved', 'user-reply', appeal='like')
    complete(tmp_path, 'one')
    for kwargs in ({}, {'appeal': 'beautiful'}, {'association': 'maybe'}):
        with pytest.raises(ValueError):
            record(tmp_path, 'one', 'user-reply', **kwargs)
    with pytest.raises(ValueError):
        record(tmp_path, 'one', '', appeal='like')
    assert stats(tmp_path)['runs_with_response'] == 0


def test_corrupt_response_is_not_silently_replaced_or_counted_as_missing(tmp_path):
    complete(tmp_path, 'one')
    path = location(tmp_path, 'one') / 'feedback.json'
    path.write_text('{broken')
    with pytest.raises(ValueError):
        record(tmp_path, 'one', 'user-reply', appeal='like')
    with pytest.raises(ValueError):
        stats(tmp_path)
    assert path.read_text() == '{broken'
