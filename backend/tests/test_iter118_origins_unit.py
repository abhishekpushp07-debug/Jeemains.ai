"""TEST-ONLY iteration 118: pure unit tests for tejas/origins.py (no DB, no network)."""
import logging, sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tejas.origins import normalise_origin, configured_origins, origin_allowed  # noqa: E402

CANON = 'https://jeelive.ai'


# --- normalisation (accepted) ---
@pytest.mark.parametrize('raw,expected', [
    ('https://jeelive.ai', CANON),
    ('  https://jeelive.ai  ', CANON),
    ('https://jeelive.ai/', CANON),
    ('HTTPS://JeeLive.AI', CANON),
    ('https://jeelive.ai:443', CANON),
    ('http://localhost:80', 'http://localhost'),
    ('http://localhost:3000', 'http://localhost:3000'),
    ('https://jeelive.ai:8443', 'https://jeelive.ai:8443'),
    ('https://[::1]:8443', 'https://[::1]:8443'),
    ('https://[2001:DB8::1]', 'https://[2001:db8::1]'),
])
def test_normalise_accepts(raw, expected):
    assert normalise_origin(raw) == expected


# --- normalisation (rejected) ---
@pytest.mark.parametrize('raw', [
    'null', '', '   ', 'https://jeelive.ai/path', 'https://jeelive.ai/?q=1', 'https://jeelive.ai?q', 'https://jeelive.ai#f',
    'https://user@jeelive.ai', 'https://user:pw@jeelive.ai', 'https://*.jeelive.ai', '*', 'https://jeelive.ai:abc',
    'https://jeelive.ai:99999', 'https://jeelive.ai:0', 'https://jee\tlive.ai', 'https://jeelive.ai\r\nX: y', 'https://jeelive.ai\x00',
    'https://jeelive.ai\x7f', 'ftp://jeelive.ai', 'jeelive.ai', '//jeelive.ai', 'https://', 'https://jeelive.ai\\@evil.com',
    'javascript://jeelive.ai',
])
def test_normalise_rejects(raw):
    with pytest.raises(ValueError):
        normalise_origin(raw)


# Malformed port text must never normalize into an allowed origin.
@pytest.mark.parametrize('raw', ['https://jeelive.ai:', 'https://jeelive.ai:0443', 'https://jeelive.ai:+443',
                                 'https://jeelive.ai:４４３', 'https://jeelive.ai:٤٤٣', 'https://[::1]:',
                                 'https://[::1]:0443', 'https://[::1]invalid'])
def test_malformed_port_probe(raw):
    with pytest.raises(ValueError):
        normalise_origin(raw)


# --- configured_origins ---
def test_configured_canonical_only():
    assert configured_origins('https://jeelive.ai/') == [CANON]


def test_configured_csv_dedup_and_wildcard_ignored(caplog):
    with caplog.at_level(logging.WARNING):
        out = configured_origins('https://jeelive.ai', ' * , https://www.jeelive.ai/ ,https://jeelive.ai:443,, http://localhost:3000 ')
    assert out == [CANON, 'https://www.jeelive.ai', 'http://localhost:3000']
    assert '*' not in out
    assert any('Wildcard' in r.message for r in caplog.records)


def test_configured_star_only_is_canonical():
    assert configured_origins(CANON, '*') == [CANON]


@pytest.mark.parametrize('fe,extra', [
    ('', None), ('*', None), ('https://jeelive.ai/app', None), (CANON, 'https://*.jeelive.ai'),
    (CANON, 'https://evil.com/path'), (CANON, 'null'), ('https://u:secretpw@jeelive.ai', None),
])
def test_configured_fails_closed_without_leaking(fe, extra):
    with pytest.raises(RuntimeError) as ei:
        configured_origins(fe, extra)
    msg = str(ei.value) + str(ei.value.__cause__)
    assert 'secretpw' not in msg and 'evil.com' not in msg


def test_configured_missing_frontend_none():
    with pytest.raises((RuntimeError, TypeError, AttributeError)):
        configured_origins(None)


# --- origin_allowed (request side) ---
ALLOWED = configured_origins(CANON, 'https://www.jeelive.ai,https://staging.jeelive.ai:8443')


@pytest.mark.parametrize('origin', [CANON, 'https://jeelive.ai:443', 'https://JEELIVE.ai', 'https://www.jeelive.ai',
                                    'https://staging.jeelive.ai:8443'])
def test_origin_allowed_true(origin):
    assert origin_allowed(origin, ALLOWED) is True


@pytest.mark.parametrize('origin', [None, '', 'null', 'http://jeelive.ai', 'https://jeelive.ai.evil.com', 'https://evil-jeelive.ai',
                                    'https://xjeelive.ai', 'https://evil.com/https://jeelive.ai', 'https://jeelive.ai@evil.com',
                                    'https://evil.com#https://jeelive.ai', 'https://staging.jeelive.ai', 'https://staging.jeelive.ai:8444',
                                    'https://sub.jeelive.ai', 'https://jeelive.ai.', 'https://jeelive%2eai', '*', 123])
def test_origin_allowed_false(origin):
    assert origin_allowed(origin, ALLOWED) is False
