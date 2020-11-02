import os
import pytest


@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))
