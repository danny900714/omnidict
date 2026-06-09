import pytest
from pytest import Parser, Config, Item


def pytest_addoption(parser: Parser):
    parser.addoption(
        "--generate-test-data", help="the provider id to generate test data for"
    )


def pytest_collection_modifyitems(config: Config, items: list[Item]):
    # If --generate-test-data option is set, skip all tests that don't have the generatetestdata marker
    # Otherwise, skip all tests that have the generatetestdata marker
    if config.getoption("generate_test_data") is not None:
        skip_non_generate = pytest.mark.skip(
            reason="skip test when --generate-test-data option is set"
        )
        for item in items:
            if "generatetestdata" not in item.keywords:
                item.add_marker(skip_non_generate)
    else:
        skip_generate = pytest.mark.skip(
            reason="skip test when --generate-test-data option is not set"
        )
        for item in items:
            if "generatetestdata" in item.keywords:
                item.add_marker(skip_generate)
