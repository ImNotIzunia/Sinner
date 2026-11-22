from sinner import __version__
from sinner.cogs.updater import parse_version


def test_parse_simple():
    assert parse_version("v1.2.3") == (1, 2, 3)
    assert parse_version("1.2.3") == (1, 2, 3)


def test_trailing_zeros_ignored():
    assert parse_version("1.2") == parse_version("1.2.0") == parse_version("v1.2.0")


def test_numeric_not_lexical_comparison():
    assert parse_version("v0.10.0") > parse_version("v0.9.9")


def test_invalid_returns_none():
    assert parse_version("latest") is None
    assert parse_version("") is None


def test_code_version_is_valid():
    assert parse_version(__version__) is not None
