"""
Test utility functions in the src.utils.utils module.
"""

from unittest.mock import patch

from src.utils.utils import (
    check_if_special_user,
    check_requests,
    format_change,
)


def test_check_requests():
    """
    Test the check_requests function to ensure it handles valid and invalid URLs correctly.
    """
    # Test with a valid URL
    valid_url = "https://jsonplaceholder.typicode.com/posts/1"
    response = check_requests(valid_url)
    assert response is not None, "Expected a valid response for a valid URL"

    # Test with an invalid URL
    invalid_url = "https://invalid-url.example.com"
    response = check_requests(invalid_url)
    assert response is None, "Expected None for an invalid URL"


def test_format_change():
    """
    Test the format_change function to ensure it formats changes correctly.
    """
    # Test with a positive change
    assert format_change(5.1234) == "🟢 +5.12%", "Expected formatted positive change"

    # Test with a negative change
    assert format_change(-3.5678) == "🔴 -3.57%", "Expected formatted negative change"

    # Test with None
    assert format_change(None) == "N/A", "Expected 'N/A' for None change"


def test_check_if_special_user():
    """
    Test the check_if_special_user function to ensure it correctly identifies special users.
    """

    with patch("src.handlers.load_variables_handler.load_json") as mock_load:
        mock_load.return_value = {"TELEGRAM_CHAT_ID_FULL_DETAILS": [12345, 67890]}

        # Test with a special user ID
        assert check_if_special_user(12345) is True, "Expected True for special user ID"

        # Test with a non-special user ID
        assert (
            check_if_special_user(11111) is False
        ), "Expected False for non-special user ID"
