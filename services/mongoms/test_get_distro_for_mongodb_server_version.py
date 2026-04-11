from services.mongoms.get_distro_for_mongodb_server_version import (
    get_distro_for_mongodb_server_version,
)


def test_mongodb_7x_latest_returns_amazon2023():
    assert get_distro_for_mongodb_server_version("v7.0-latest") == "amazon2023"


def test_mongodb_7011_returns_amazon2023():
    assert get_distro_for_mongodb_server_version("7.0.11") == "amazon2023"


def test_mongodb_821_returns_amazon2023():
    assert get_distro_for_mongodb_server_version("8.2.1") == "amazon2023"


def test_mongodb_609_returns_amazon2():
    assert get_distro_for_mongodb_server_version("6.0.9") == "amazon2"


def test_mongodb_6014_returns_amazon2():
    assert get_distro_for_mongodb_server_version("6.0.14") == "amazon2"


def test_unparseable_version_defaults_to_amazon2023():
    assert get_distro_for_mongodb_server_version("latest") == "amazon2023"
