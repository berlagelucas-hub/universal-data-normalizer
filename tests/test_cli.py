from universal_data_normalizer.cli import get_version


def test_version():
    assert get_version() == "0.1.0"
