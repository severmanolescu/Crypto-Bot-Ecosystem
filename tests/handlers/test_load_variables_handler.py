"""
Test suite for the load_variables_handler module.
Tests loading and saving of configuration variables from/to JSON files.
"""

# pylint: disable=attribute-defined-outside-init,unused-variable

import json
import os
from unittest.mock import mock_open, patch

from src.handlers.load_variables_handler import (
    get_all_symbols,
    get_int_variable,
    get_json_key_value,
    load_json,
    load_keyword_list,
    load_portfolio_from_file,
    load_symbol_to_id,
    load_transactions,
)


class TestLoadVariables:
    """Tests for loading variables from JSON files."""

    def setup_method(self):
        """Initialize the test class."""
        self.dummy_path = "./tests/test_files/dummy_path.json"

    def __del__(self):
        """Clean up the test class."""
        if os.path.exists(self.dummy_path):
            os.remove(self.dummy_path)

    def test_load_existing_file(self):
        """Test loading from an existing JSON file."""
        mock_data = {"KEY1": "value1", "KEY2": 2}
        mock_file = mock_open(read_data=json.dumps(mock_data))

        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_file
        ):
            result = load_json(self.dummy_path)

            assert result == mock_data, "Expected loaded data to match mock data"
            mock_file.assert_called_once_with(self.dummy_path, "r", encoding="utf-8")

    def test_load_nonexistent_file(self):
        """Test loading from a nonexistent file."""
        with patch("os.path.exists", return_value=False):
            result = load_json("nonexistent.json")

            assert result == {}, "Expected empty dict for nonexistent file"

    def test_load_invalid_json(self):
        """Test loading from a file with invalid JSON."""
        invalid_json = "{ this is not valid json }"
        mock_file = mock_open(read_data=invalid_json)

        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_file
        ):
            result = load_json("invalid.json")

            assert result == {}, "Expected empty dict for invalid JSON"


class TestGetJsonKeyValue:
    """Tests for retrieving specific values from JSON files."""

    def setup_method(self):
        """Initialize the test class."""
        self.test_file_path = "./tests/test_files/test_path.json"

    def __del__(self):
        """Clean up the test class."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_get_existing_key(self):
        """Test retrieving an existing key from a JSON file."""
        mock_data = {"KEY1": "value1", "KEY2": 2}
        mock_file = mock_open(read_data=json.dumps(mock_data))

        with patch("os.path.isfile", return_value=True), patch(
            "builtins.open", mock_file
        ):
            result = get_json_key_value("KEY1", self.test_file_path)

            assert result == "value1", "Expected value to match the mock data"

    def test_get_nonexistent_key(self):
        """Test retrieving a nonexistent key from a JSON file."""
        mock_data = {"KEY1": "value1"}
        mock_file = mock_open(read_data=json.dumps(mock_data))

        with patch("os.path.isfile", return_value=True), patch(
            "builtins.open", mock_file
        ), patch("builtins.print"):
            result = get_json_key_value("NONEXISTENT", self.test_file_path)

            assert result is None, "Expected result to be None for nonexistent key"

    def test_get_from_nonexistent_file(self):
        """Test retrieving a key from a nonexistent file."""
        with patch("os.path.isfile", return_value=False), patch("builtins.print"):
            result = get_json_key_value("KEY1", "nonexistent.json")

            assert result is None, "Expected result to be None for nonexistent file"

    def test_get_from_invalid_json(self):
        """Test retrieving a key from a file with invalid JSON."""
        invalid_json = "{ this is not valid json }"
        mock_file = mock_open(read_data=invalid_json)

        with patch("os.path.isfile", return_value=True), patch(
            "builtins.open", mock_file
        ), patch("builtins.print"):
            result = get_json_key_value("KEY1", "invalid.json")

            assert result is None, "Expected result to be None for invalid JSON"


class TestGetIntVariable:
    """Tests for retrieving integer variables."""

    def test_get_int_variable_int(self):
        """Test getting an integer variable that is already an integer."""
        with patch(
            "src.handlers.load_variables_handler.load_json",
            return_value={"TEST_VAR": 42},
        ):
            result = get_int_variable("TEST_VAR", default=10)
            assert result == 42, "Expected result to be the integer value"

    def test_get_int_variable_string(self):
        """Test getting an integer variable that is stored as a string."""
        with patch(
            "src.handlers.load_variables_handler.load_json",
            return_value={"TEST_VAR": "42"},
        ):
            result = get_int_variable("TEST_VAR", default=10)
            assert result == 42, "Expected result to be the integer value from string"

    def test_get_int_variable_invalid_string(self):
        """Test getting an invalid string that can't be converted to an integer."""
        with patch(
            "src.handlers.load_variables_handler.load_json",
            return_value={"TEST_VAR": "not_an_int"},
        ), patch("builtins.print"):
            result = get_int_variable("TEST_VAR", default=10)
            assert (
                result == 10
            ), "Expected result to be the default value for invalid string"

    def test_get_int_variable_missing(self):
        """Test getting a variable that doesn't exist."""
        with patch("src.handlers.load_variables_handler.load_json", return_value={}):
            result = get_int_variable("MISSING_VAR", default=10)
            assert (
                result == 10
            ), "Expected result to be the default value for missing variable"

    def test_get_int_variable_invalid_type(self):
        """Test getting a variable with an invalid type."""
        with patch(
            "src.handlers.load_variables_handler.load_json",
            return_value={"TEST_VAR": [1, 2, 3]},
        ), patch("builtins.print"):
            result = get_int_variable("TEST_VAR", default=10)
            assert (
                result == 10
            ), "Expected result to be the default value for invalid type"


class TestPortfolioFunctions:
    """Tests for portfolio-related functions."""

    def setup_method(self):
        """Initialize the test class."""
        self.test_file_path = "./tests/test_files/portfolio.json"

    def __del__(self):
        """Clean up the test class."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_load_portfolio_existing_file(self):
        """Test loading portfolio from an existing file."""
        mock_data = [{"symbol": "BTC", "amount": 0.5}]
        mock_file = mock_open(read_data=json.dumps(mock_data))

        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_file
        ), patch("builtins.print"):
            result = load_portfolio_from_file(self.test_file_path)

            assert result == mock_data, "Expected portfolio data to match mock data"

    def test_load_portfolio_nonexistent_file(self):
        """Test loading portfolio from a nonexistent file."""
        with patch("os.path.exists", return_value=False), patch("builtins.print"):
            result = load_portfolio_from_file("nonexistent.json")

            assert result == [], "Expected empty list for nonexistent file"

    def test_load_portfolio_invalid_json(self):
        """Test loading portfolio from a file with invalid JSON."""
        invalid_json = "{ this is not valid json }"
        mock_file = mock_open(read_data=invalid_json)

        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_file
        ), patch("builtins.print"):
            result = load_portfolio_from_file("invalid.json")

            assert result == [], "Expected empty list for invalid JSON"


class TestTransactionFunctions:
    """Tests for transaction-related functions."""

    def setup_method(self):
        """Initialize the test class."""
        self.test_file_path = "./tests/test_files/transactions.json"

    def __del__(self):
        """Clean up the test class."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_load_transactions_existing_file(self):
        """Test loading transactions from an existing file."""
        mock_data = [{"symbol": "BTC", "action": "BUY", "amount": 0.5, "price": 50000}]
        mock_file = mock_open(read_data=json.dumps(mock_data))

        with patch("builtins.open", mock_file):
            result = load_transactions(self.test_file_path)

            assert (
                result == mock_data
            ), "Expected loaded transactions to match mock data"

    def test_load_transactions_nonexistent_file(self):
        """Test loading transactions from a nonexistent file."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = load_transactions("nonexistent.json")

            assert result == [], "Expected empty list for nonexistent file"

    def test_load_transactions_invalid_json(self):
        """Test loading transactions from a file with invalid JSON."""
        with patch(
            "builtins.open", side_effect=json.JSONDecodeError("Expecting value", "", 0)
        ):
            result = load_transactions("invalid.json")

            assert result == [], "Expected empty list for invalid JSON"


class TestKeywordFunctions:
    """Tests for keyword-related functions."""

    def setup_method(self):
        """Initialize the test class."""
        self.test_file_path = "./tests/test_files/keywords.json"

    def __del__(self):
        """Clean up the test class."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_load_keyword_list_existing_file(self):
        """Test loading keywords from an existing file."""
        mock_data = ["bitcoin", "ethereum", "blockchain"]
        mock_file = mock_open(read_data=json.dumps(mock_data))

        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_file
        ), patch("builtins.print"):
            result = load_keyword_list(self.test_file_path)

            assert result == mock_data, "Expected loaded keywords to match mock data"

    def test_load_keyword_list_nonexistent_file(self):
        """Test loading keywords from a nonexistent file."""
        with patch("os.path.exists", return_value=False), patch("builtins.print"):
            result = load_keyword_list("nonexistent.json")

            assert result == [], "Expected empty list for nonexistent file"

    def test_load_keyword_list_invalid_json(self):
        """Test loading keywords from a file with invalid JSON."""
        invalid_json = "{ this is not valid json }"
        mock_file = mock_open(read_data=invalid_json)

        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_file
        ), patch("builtins.print"):
            result = load_keyword_list("invalid.json")

            assert result == [], "Expected empty list for invalid JSON"

    def test_load_keyword_list_not_a_list(self):
        """Test loading keywords from a file that doesn't contain a list."""
        mock_data = {"keywords": ["bitcoin", "ethereum"]}  # Not a list, but a dict
        mock_file = mock_open(read_data=json.dumps(mock_data))

        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_file
        ), patch("builtins.print"):
            result = load_keyword_list("not_a_list.json")

            assert result == [], "Expected empty list for non-list JSON structure"


class TestSymbolFunctions:
    """Tests for symbol-related functions."""

    def setup_method(self):
        """Initialize the test class."""
        self.test_file_path = "./tests/test_files/symbol_to_id.json"

    def __del__(self):
        """Clean up the test class."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_load_symbol_to_id_existing_file(self):
        """Test loading symbol-to-id mapping from an existing file."""
        mock_data = {"BTC": "bitcoin", "ETH": "ethereum"}
        mock_file = mock_open(read_data=json.dumps(mock_data))

        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_file
        ), patch("builtins.print"):
            result = load_symbol_to_id(self.test_file_path)

            assert (
                result == mock_data
            ), "Expected loaded symbol-to-id mapping to match mock data"

    def test_load_symbol_to_id_nonexistent_file(self):
        """Test loading symbol-to-id mapping from a nonexistent file."""
        with patch("os.path.exists", return_value=False), patch("builtins.print"):
            result = load_symbol_to_id("nonexistent.json")

            assert result == {}, "Expected empty dict for nonexistent file"

    def test_load_symbol_to_id_invalid_json(self):
        """Test loading symbol-to-id mapping from a file with invalid JSON."""
        invalid_json = "{ this is not valid json }"
        mock_file = mock_open(read_data=invalid_json)

        with patch("os.path.exists", return_value=True), patch(
            "builtins.open", mock_file
        ), patch("builtins.print"):
            result = load_symbol_to_id("invalid.json")

            assert result == {}, "Expected empty dict for invalid JSON"

    def test_get_all_symbols(self):
        """Test getting all unique symbols from transactions."""
        transactions = [
            {"symbol": "BTC", "action": "BUY"},
            {"symbol": "ETH", "action": "BUY"},
            {"symbol": "BTC", "action": "SELL"},  # Duplicate symbol
        ]

        with patch(
            "src.handlers.load_variables_handler.load_transactions",
            return_value=transactions,
        ):
            result = get_all_symbols()

            # Set to list conversion makes order non-deterministic, so we sort both
            assert sorted(result) == sorted(
                ["BTC", "ETH"]
            ), "Expected unique symbols to be returned"

    def test_get_all_symbols_empty_transactions(self):
        """Test getting symbols when transactions are empty."""
        with patch(
            "src.handlers.load_variables_handler.load_transactions", return_value=[]
        ):
            result = get_all_symbols()
            assert not result, "Expected empty list when no transactions are present"

    def test_get_all_symbols_invalid_transactions(self):
        """Test getting symbols when transactions are invalid."""
        invalid_transactions = [
            {"not_a_symbol": "BTC"},  # Missing symbol
            "not_a_dict",  # Not a dict
            {"symbol": "ETH"},  # Valid
        ]

        with patch(
            "src.handlers.load_variables_handler.load_transactions",
            return_value=invalid_transactions,
        ):
            result = get_all_symbols()
            assert result == ["ETH"], "Expected only valid symbols to be returned"
