import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "only: Run only the tests marked with only."
    )
