"""Integration tests for vision.py with OpenAI"""

import os

import pytest

from services.openai.vision import describe_image


@pytest.mark.skipif(bool(os.getenv("CI")), reason="Skip integration tests in CI")
def test_describe_image_integration():
    """Test describe_image function with real OpenAI API call"""
    # Simple 1x1 red pixel image (just base64 string, not data URL)
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    response = describe_image(base64_image)

    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.skipif(bool(os.getenv("CI")), reason="Skip integration tests in CI")
def test_describe_image_with_context():
    """Test describe_image with context parameter"""
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    response = describe_image(base64_image, "This is a test image")

    assert isinstance(response, str)
    assert len(response) > 0
