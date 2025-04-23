from unittest import mock

import pytest
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MAX_RETRIES, OPENAI_ORG_ID
from services.openai.init import create_openai_client


def test_create_openai_client():
    client = create_openai_client()
    
    assert isinstance(client, OpenAI)
    assert client.api_key == OPENAI_API_KEY
    assert client.max_retries == OPENAI_MAX_RETRIES
    assert client.organization == OPENAI_ORG_ID


@mock.patch("services.openai.init.OpenAI")
def test_create_openai_client_with_mock(mock_openai):
    mock_client = mock.MagicMock()
    mock_openai.return_value = mock_client
    
    client = create_openai_client()
    
    mock_openai.assert_called_once_with(
        api_key=OPENAI_API_KEY,
        max_retries=OPENAI_MAX_RETRIES,
        organization=OPENAI_ORG_ID,
    )
    assert client == mock_client


@mock.patch("services.openai.init.OPENAI_API_KEY", "test_api_key")
@mock.patch("services.openai.init.OPENAI_MAX_RETRIES", 5)
@mock.patch("services.openai.init.OPENAI_ORG_ID", "test_org_id")
@mock.patch("services.openai.init.OpenAI")
def test_create_openai_client_with_different_config(mock_openai):
    create_openai_client()
    
    mock_openai.assert_called_once_with(
        api_key="test_api_key",
        max_retries=5,
        organization="test_org_id",
    )
from unittest import mock

import pytest
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MAX_RETRIES, OPENAI_ORG_ID
from services.openai.init import create_openai_client


def test_create_openai_client():
    client = create_openai_client()
    
    assert isinstance(client, OpenAI)
    assert client.api_key == OPENAI_API_KEY
    assert client.max_retries == OPENAI_MAX_RETRIES
    assert client.organization == OPENAI_ORG_ID


@mock.patch("services.openai.init.OpenAI")
def test_create_openai_client_with_mock(mock_openai):
    mock_client = mock.MagicMock()
    mock_openai.return_value = mock_client
    
    client = create_openai_client()
    
    mock_openai.assert_called_once_with(
        api_key=OPENAI_API_KEY,
        max_retries=OPENAI_MAX_RETRIES,
        organization=OPENAI_ORG_ID,
    )
    assert client == mock_client


@mock.patch("services.openai.init.OPENAI_API_KEY", "test_api_key")
@mock.patch("services.openai.init.OPENAI_MAX_RETRIES", 5)
@mock.patch("services.openai.init.OPENAI_ORG_ID", "test_org_id")
@mock.patch("services.openai.init.OpenAI")
def test_create_openai_client_with_different_config(mock_openai):
    create_openai_client()
    
    mock_openai.assert_called_once_with(
        api_key="test_api_key",
        max_retries=5,
        organization="test_org_id",
    )


def test_create_openai_client_integration():
    client = create_openai_client()
    
    assert client.api_key == OPENAI_API_KEY
    assert client.max_retries == OPENAI_MAX_RETRIES
    assert client.organization == OPENAI_ORG_ID
    
    # Verify client has expected attributes and methods
    assert hasattr(client, "chat")
    assert hasattr(client, "completions")
