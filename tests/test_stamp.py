import stamp


def test_version():
    assert stamp.__version__ is not None
    assert isinstance(stamp.__version__, str)
