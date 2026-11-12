"""The retained-API-image sweep proves itself from a witness row, so a start-up whose images are
all still named costs no messages scan — and never keeps bytes a transcript stopped naming.

Background: the sweep ran one unindexable ``instr()`` pass over every transcript row on every
gateway start-up. On the live store (143k rows / 153 MB) that pass blocked the event loop long
enough for the liveness watchdog to exit the gateway, which the supervisor then restarted into the
same pass. Confirming a witness is a primary-key lookup instead.
"""
from pathlib import Path

import pytest

from gateway.session_ingress_media import _WITNESS_PREFIX, _media_root, collect_unheld_api_images
from hermes_state_keys import prefix_range
from tests.gateway.test_retired_media_scan_bound import _trace_messages_scans


@pytest.fixture
def home(owner, tmp_path, monkeypatch):
    """``owner``'s store as the ACTIVE home, which the sweep requires before it collects anything."""
    monkeypatch.setenv('HERMES_HOME', str(tmp_path))
    return owner


def _plant(count=1):
    root = _media_root()
    planted = []
    for index in range(count):
        digest = f'{index:064x}'
        path = root / digest / f'api_{digest[:32]}.png'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'img' + index.to_bytes(4, 'big'))
        planted.append((digest, path))
    return planted


def _name_in_transcript(db, planted, session='keeper'):
    """One transcript row per image, spelling it the way a note does."""
    if db.get_session(session) is None:
        db.create_session(session, source='cli')
    for digest, path in planted:
        db.append_message(session, 'user', f'[Image attached at: {digest}/{path.name}]')


def _witnesses(db):
    return {str(row['key'])[len(_WITNESS_PREFIX):]: str(row['value']) for row in db._read_all(
        'SELECT key,value FROM state_meta WHERE key>=? AND key<?', prefix_range(_WITNESS_PREFIX))}


def _full_scans(traced):
    """Only the unbounded passes: the under-lock re-check carries ``id>`` and is indexed."""
    return [sql for sql in traced if 'id>' not in sql.replace(' ', '')]


def _alive(planted):
    return [digest for digest, path in planted if path.exists()]


def test_a_named_image_is_confirmed_next_time_without_scanning_again(home):
    """The point of the change: the second sweep reaches the same answer with no messages pass."""
    planted = _plant()
    _name_in_transcript(home.db, planted)

    first = _trace_messages_scans(home.db)
    assert collect_unheld_api_images(home.db) == 0
    assert len(_full_scans(first)) == 1, 'the first sweep has nothing recorded yet, so it must scan'
    assert _witnesses(home.db).keys() == {planted[0][0]}, 'the naming row must be remembered'

    second = _trace_messages_scans(home.db)
    assert collect_unheld_api_images(home.db) == 0
    assert _full_scans(second) == [], 'a witnessed image must not be re-proved by a table scan'
    assert _alive(planted) == [planted[0][0]]


def test_an_unnamed_image_is_collected_and_remembers_nothing(home):
    planted = _plant()
    home.db.create_session('empty', source='cli')
    home.db.append_message('empty', 'user', 'nothing about any image here')

    assert collect_unheld_api_images(home.db) == 1
    assert _alive(planted) == []
    assert _witnesses(home.db) == {}, 'a collected image must leave no witness row behind'


def test_a_witness_whose_row_was_deleted_falls_back_to_the_scan(home):
    """A stale witness must cost a scan, not an answer: the image is still named elsewhere."""
    planted = _plant()
    digest, path = planted[0]
    _name_in_transcript(home.db, planted)
    collect_unheld_api_images(home.db)
    witness = int(_witnesses(home.db)[digest])

    _name_in_transcript(home.db, planted, session='second')
    home.db._execute_write(lambda conn: conn.execute('DELETE FROM messages WHERE id=?', (witness,)))

    traced = _trace_messages_scans(home.db)
    assert collect_unheld_api_images(home.db) == 0
    assert len(_full_scans(traced)) == 1, 'a vanished witness must be re-proved, not trusted'
    assert path.exists()
    assert int(_witnesses(home.db)[digest]) != witness, 'the surviving row becomes the new witness'


def test_a_rewritten_row_that_drops_the_name_frees_the_image(home):
    """The safety case. ``session_results`` and ``transcript_repair`` rewrite ``content`` in place,
    so a witness id alone is never proof; the needle has to still be in the row."""
    planted = _plant()
    digest = planted[0][0]
    _name_in_transcript(home.db, planted)
    collect_unheld_api_images(home.db)
    witness = int(_witnesses(home.db)[digest])

    home.db._execute_write(lambda conn: conn.execute(
        'UPDATE messages SET content=? WHERE id=?', ('the image reference is gone', witness)))

    assert collect_unheld_api_images(home.db) == 1, 'a cached yes must not outlive the mention'
    assert _alive(planted) == []
    assert _witnesses(home.db) == {}


def test_a_thousand_witnessed_images_stay_within_sqlites_limits(home):
    """The witness lookup must not grow its statement with the image count either (#140090)."""
    planted = _plant(1010)
    _name_in_transcript(home.db, planted)
    assert collect_unheld_api_images(home.db) == 0
    assert len(_witnesses(home.db)) == 1010

    traced = _trace_messages_scans(home.db)
    assert collect_unheld_api_images(home.db) == 0
    assert _full_scans(traced) == []
    assert len(_alive(planted)) == 1010


def test_an_image_named_only_by_a_post_snapshot_row_is_remembered_too(home):
    """A mention found by the under-lock re-check is as good a witness as one from the snapshot."""
    import gateway.session_ingress_media as media

    planted = _plant()
    digest, path = planted[0]
    home.db.create_session('keeper', source='cli')
    original = media._history_mentions

    def mention_late(conn, references, after_id=0):
        """Stands in for a row inserted between the snapshot and the write lock: nothing for the
        snapshot pass, found by the under-lock re-check. Staging the real insert would need a hook
        inside the write transaction; what matters here is which pass supplies the witness."""
        return {} if not after_id else original(conn, references)

    _name_in_transcript(home.db, planted)
    media._history_mentions = mention_late
    try:
        assert collect_unheld_api_images(home.db) == 0
    finally:
        media._history_mentions = original
    assert path.exists()
    assert _witnesses(home.db).keys() == {digest}

    traced = _trace_messages_scans(home.db)
    assert collect_unheld_api_images(home.db) == 0
    assert _full_scans(traced) == []
