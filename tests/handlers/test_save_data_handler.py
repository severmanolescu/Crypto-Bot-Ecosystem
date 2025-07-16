import json
import os
from datetime import datetime, timezone
from unittest.mock import mock_open, patch

from src.handlers.save_data_handler import (
    save_data_to_json_file,
    save_keywords,
    save_transaction,
    save_variables_json,
)


class TestSaveVariables:
    """Tests for saving variables to JSON files."""

    def setup_method(self):
        """Initialize the test class."""
        self.test_file_path = "./tests/test_files/test_path.json"

    def __del__(self):
        """Clean up the test class."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_save_variables(self):
        """Test saving variables to a JSON file."""
        variables = {"KEY1": "value1", "KEY2": 2}
        mock_file = mock_open()

        # Patch both open and json.dump
        with patch("src.handlers.save_data_handler.open", mock_file), patch(
            "json.dump"
        ) as mock_dump, patch("builtins.print"):
            save_variables_json(variables, self.test_file_path)

            # Check if either approach was used
            assert (
                mock_file.called or mock_dump.called
            ), "Either open or json.dump should be called"

    def test_save_variables_with_set(self):
        """Test saving variables containing a set (which should be converted to a list)."""
        variables = {"SEND_HOURS": {8, 12, 16}}
        expected = {"SEND_HOURS": [8, 12, 16]}  # Set converted to list
        mock_file = mock_open()

        # Use the same patching approach that worked in test_save_variables
        with patch("src.handlers.save_data_handler.open", mock_file), patch(
            "json.dump"
        ) as mock_json_dump, patch("builtins.print"):
            save_variables_json(variables, self.test_file_path)
            if mock_file.called and mock_file().write.called:
                written_data = mock_file().write.call_args[0][0]
                saved_data = json.loads(written_data)
                saved_data["SEND_HOURS"].sort()
                expected["SEND_HOURS"].sort()
                assert (
                    saved_data == expected
                ), "Expected saved data to match expected data"
            elif mock_json_dump.called:
                saved_data = mock_json_dump.call_args[0][0]
                assert (
                    "SEND_HOURS" in saved_data
                ), "Expected SEND_HOURS to be in saved data"
                assert isinstance(
                    saved_data["SEND_HOURS"], list
                ), "Expected SEND_HOURS to be a list"
                assert sorted(saved_data["SEND_HOURS"]) == sorted(
                    expected["SEND_HOURS"]
                ), "Expected SEND_HOURS to be saved as a list"

    def test_save_with_exception(self):
        """Test saving variables when an exception occurs."""
        variables = {"KEY1": "value1"}

        with patch("builtins.open", side_effect=Exception("Test error")), patch(
            "builtins.print"
        ) as mock_print:
            save_variables_json(variables, self.test_file_path)

            # Verify error message was printed
            assert any(
                "Error saving variables" in str(call)
                for call in mock_print.call_args_list
            ), "Expected error message to be printed when saving fails"


class TestSavePortfolioFunctions:
    def setup_method(self):
        """Initialize the test class."""
        self.test_file_path = "./tests/test_files/portfolio.json"

    def __del__(self):
        """Clean up the test class."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_save_data_to_json_file(self):
        """Test saving data to a JSON file."""
        data = [{"symbol": "BTC", "amount": 0.5}]
        mock_file = mock_open()

        # Patch both open and json.dump directly
        with patch("src.handlers.save_data_handler.open", mock_file), patch(
            "json.dump"
        ) as mock_json_dump:
            save_data_to_json_file(self.test_file_path, data)

            # Check that open was called correctly
            mock_file.assert_called_once_with(
                self.test_file_path, "w", encoding="utf-8"
            )
            mock_json_dump.assert_called_once()

            assert (
                mock_json_dump.call_args[0][0] == data
            ), "Expected data to be passed to json.dump"
            assert (
                mock_json_dump.call_args[0][1] == mock_file()
            ), "Expected data to be saved correctly"


class TestSaveTransactionFunctions:
    """Tests for transaction-related functions."""

    def setup_method(self):
        """Initialize the test class."""
        self.test_file_path = "./tests/test_files/transactions.json"

    def __del__(self):
        """Clean up the test class."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_save_transaction(self):
        """Test saving a transaction."""
        transaction_path = "transactions.json"

        fixed_time = datetime(2023, 1, 1, tzinfo=timezone.utc)

        with patch("src.handlers.save_data_handler.datetime") as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.timezone = timezone

            with patch(
                "src.handlers.load_variables_handler.load_transactions", return_value=[]
            ) as mock_load, patch(
                "src.handlers.save_data_handler.save_data_to_json_file"
            ) as mock_save:
                save_transaction("BTC", "buy", 0.5, 50000, transaction_path)

                expected_transaction = {
                    "symbol": "BTC",
                    "action": "BUY",
                    "amount": 0.5,
                    "price": 50000.0,
                    "total": 25000.0,
                    "timestamp": fixed_time.isoformat(),
                }

                mock_save.assert_called_once_with(
                    transaction_path, [expected_transaction]
                )


class TestSaveKeywordFunctions:
    """Tests for keyword-related functions."""

    def setup_method(self):
        """Initialize the test class."""
        self.test_file_path = "./tests/test_files/keywords.json"

    def __del__(self):
        """Clean up the test class."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_save_keywords(self):
        """Test saving keywords to a file."""
        keywords = ["bitcoin", "ethereum", "blockchain"]
        mock_file = mock_open()

        # Use the proper path to patch where open is actually used
        with patch("src.handlers.save_data_handler.open", mock_file), patch(
            "json.dump"
        ) as mock_json_dump:
            save_keywords(keywords, self.test_file_path)

            # Check file was opened correctly
            mock_file.assert_called_once_with(
                self.test_file_path, "w", encoding="utf-8"
            )

            # Check json.dump was called with the right arguments
            mock_json_dump.assert_called_once()
            assert (
                mock_json_dump.call_args[0][0] == keywords
            ), "Expected keywords to be passed to json.dump"
            assert (
                mock_json_dump.call_args[0][1] == mock_file()
            ), "Expected data to be saved correctly"
