"""Smoke tests for the package."""

import complexity_lab as cl


def test_package_importable() -> None:
    assert cl is not None


def test_version_exposed() -> None:
    assert cl.__version__ == "0.1.0"
