from app.services.challenge_store import ChallengeStore


def test_put_get_consume():
    store = ChallengeStore(ttl_seconds=100)
    cid = store.put(None, "registration", b"challenge-bytes")
    ctx = store.get(cid)
    assert ctx is not None
    assert ctx.challenge == b"challenge-bytes"
    # consuming removes it
    ctx2 = store.consume(cid)
    assert ctx2 is not None
    assert store.get(cid) is None


def test_expiry():
    store = ChallengeStore(ttl_seconds=-1)
    cid = store.put(None, "login", b"x")
    assert store.get(cid) is None
    assert store.consume(cid) is None
