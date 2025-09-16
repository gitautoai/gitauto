"""Integration tests for vision.py with GPT-5"""

import os
import pytest
from services.openai.vision import describe_image


@pytest.mark.skipif(bool(os.getenv("CI")), reason="Skip integration tests in CI")
def test_describe_image_gpt5_integration():
    """Test describe_image function with real GPT-5 API call"""
    # Simple 1x1 red pixel image (just base64 string, not data URL)
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    response = describe_image(base64_image)

    assert isinstance(response, str)
    assert len(response) > 0
    print(f"GPT-5 vision response: {response}")


@pytest.mark.skipif(bool(os.getenv("CI")), reason="Skip integration tests in CI")
def test_describe_image_gpt5_with_context():
    """Test describe_image with context parameter using GPT-5"""
    base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    response = describe_image(base64_image, "This is a test image")

    assert isinstance(response, str)
    assert len(response) > 0
    print(f"GPT-5 vision with context response: {response}")
