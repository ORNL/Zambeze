import pytest


@pytest.mark.integration
def test_dummy1_true():
    assert True


@pytest.mark.integration
def test_dummy_false():
    assert False, "This should break"
