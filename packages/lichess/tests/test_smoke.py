def test_the_package_is_importable() -> None:
    import lucia_lichess

    assert lucia_lichess.LichessExplorerClient is not None
