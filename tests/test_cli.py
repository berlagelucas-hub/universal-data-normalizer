from python_service_template.cli import get_version


def test_version():
    assert get_version() == "0.1.0"
