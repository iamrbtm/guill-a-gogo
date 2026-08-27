from app.services import crypto


def test_sha256_deterministic():
    assert crypto.sha256_hex("abc") == crypto.sha256_hex("abc")
    assert crypto.sha256_hex("abc") != crypto.sha256_hex("abd")


def test_generate_token_length_and_unique():
    a = crypto.generate_token()
    b = crypto.generate_token()
    assert a != b
    assert len(a) >= 32


def test_recovery_code_format():
    code = crypto.generate_recovery_code()
    parts = code.split("-")
    assert len(parts) == 3
    for p in parts:
        assert len(p) == 4
        assert p.isalnum()
        assert p == p.upper()


def test_constant_time_compare():
    assert crypto.constant_time_compare("a", "a") is True
    assert crypto.constant_time_compare("a", "b") is False
