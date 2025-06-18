"""
Test suite for the OpenAIPrompt class in the src.handlers.open_ai_prompt_handler module.
This suite tests the initialization and API interaction methods.
"""

# pylint: disable=redefined-outer-name

from unittest.mock import MagicMock, patch

import openai
import pytest

from src.handlers.open_ai_prompt_handler import OpenAIPrompt


@pytest.fixture
def openai_prompt():
    """Fixture to create an OpenAIPrompt instance for testing."""
    return OpenAIPrompt(openai_api_key="test_api_key")


@pytest.mark.asyncio
async def test_init():
    """Test that OpenAIPrompt initializes with the correct API key."""
    api_key = "test_api_key"
    prompt_handler = OpenAIPrompt(openai_api_key=api_key)

    assert prompt_handler.openai_api_key == api_key


@pytest.mark.asyncio
async def test_generate_summary(openai_prompt):
    """Test generating a summary for an article."""
    article_link = "https://example.com/article"
    expected_summary = (
        "<b>Summary:</b> This is a test summary. <b>Sentiment:</b> Bullish"
    )

    # Mock the get_response method
    with patch.object(
        openai_prompt, "get_response", return_value=expected_summary
    ) as mock_get_response:
        summary = await openai_prompt.generate_article_summary(article_link)

        # Verify the summary is returned correctly
        assert summary == expected_summary

        # Check that get_response was called with the correct prompt
        mock_get_response.assert_called_once()
        prompt_arg = mock_get_response.call_args[0][0]
        assert article_link in prompt_arg
        assert "Rezuma acest articol" in prompt_arg
        assert "Bullish, Bearish sau Neutral" in prompt_arg


@pytest.mark.asyncio
async def test_get_response_success(openai_prompt):
    """Test successful response generation from OpenAI API."""
    test_prompt = "Test prompt"
    expected_response = "Test response"

    # Create a mock for the OpenAI client
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = expected_response

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_completion

    # Mock the OpenAI client creation
    with patch("openai.OpenAI", return_value=mock_client):
        response = await openai_prompt.get_response(test_prompt)

        # Verify the response
        assert response == expected_response

        # Check the API was called with the correct parameters
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": test_prompt}],
            temperature=0.7,
            max_tokens=200,
        )


@pytest.mark.asyncio
async def test_get_response_with_custom_parameters(openai_prompt):
    """Test response generation with custom model and max_tokens."""
    test_prompt = "Test prompt"
    expected_response = "Test response"
    custom_model = "gpt-4"
    custom_max_tokens = 500

    # Create a mock for the OpenAI client
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = expected_response

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_completion

    # Mock the OpenAI client creation
    with patch("openai.OpenAI", return_value=mock_client):
        response = await openai_prompt.get_response(
            test_prompt, model=custom_model, max_tokens=custom_max_tokens
        )

        # Verify the response
        assert response == expected_response

        # Check the API was called with the custom parameters
        mock_client.chat.completions.create.assert_called_once_with(
            model=custom_model,
            messages=[{"role": "user", "content": test_prompt}],
            temperature=0.7,
            max_tokens=custom_max_tokens,
        )


@pytest.mark.asyncio
async def test_get_response_api_error(openai_prompt):
    """Test handling of OpenAI API errors."""
    test_prompt = "Test prompt"

    # Mock the OpenAI client to raise an exception
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = openai.OpenAIError(
            "API Error"
        )
        mock_openai.return_value = mock_client

        response = await openai_prompt.get_response(test_prompt)

        # Verify the fallback response
        assert response == "No summary available."


@pytest.mark.asyncio
async def test_get_response_value_error(openai_prompt):
    """Test handling of ValueError exceptions."""
    test_prompt = "Test prompt"

    # Mock the OpenAI client to raise ValueError
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = ValueError("Value Error")
        mock_openai.return_value = mock_client

        response = await openai_prompt.get_response(test_prompt)

        # Verify the fallback response
        assert response == "No summary available."


@pytest.mark.asyncio
async def test_get_response_type_error(openai_prompt):
    """Test handling of TypeError exceptions."""
    test_prompt = "Test prompt"

    # Mock the OpenAI client to raise TypeError
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = TypeError("Type Error")
        mock_openai.return_value = mock_client

        response = await openai_prompt.get_response(test_prompt)

        # Verify the fallback response
        assert response == "No summary available."
