"""
Test suite for the load_variables_handler module.
This module tests the loading, saving, and retrieval of variables
"""

import os

import src.handlers.load_variables_handler


def test_load_variables():
    """
    Test the loading of variables from the configuration file.
    """
    print("Testing the loading of variables...")

    # Load the variables
    variables = src.handlers.load_variables_handler.load()

    # Check if the variables are loaded correctly
    assert isinstance(variables, dict), "Variables should be loaded as a dictionary."
    assert (
        "TELEGRAM_API_TOKEN_ALERTS" in variables
    ), "TELEGRAM_API_TOKEN_ALERTS should be in the variables."
    assert (
        "ALERT_THRESHOLD_1H" in variables
    ), "ALERT_THRESHOLD_1H should be in the variables."
    assert (
        "ALERT_THRESHOLD_24H" in variables
    ), "ALERT_THRESHOLD_24H should be in the variables."
    assert (
        "ALERT_THRESHOLD_7D" in variables
    ), "ALERT_THRESHOLD_7D should be in the variables."
    assert (
        "ALERT_THRESHOLD_30D" in variables
    ), "ALERT_THRESHOLD_30D should be in the variables."


def test_save_variables():
    """
    Test the saving of variables to the configuration file.
    """
    print("Testing the saving of variables...")

    # Load the variables
    variables = src.handlers.load_variables_handler.load()

    # Modify a variable
    variables["TEST_VARIABLE"] = "Test Value"

    # Save the modified variables
    src.handlers.load_variables_handler.save(variables)

    # Reload the variables to check if the change was saved
    reloaded_variables = src.handlers.load_variables_handler.load()

    assert (
        reloaded_variables["TEST_VARIABLE"] == "Test Value"
    ), "The TEST_VARIABLE should be saved correctly."


def test_get_json_key_value():
    """
    Test the get_json_key_value function from load_variables_handler.
    """
    print("Testing the get_json_key_value function...")

    # Check if a known key exists
    value = src.handlers.load_variables_handler.get_json_key_value(
        "TELEGRAM_API_TOKEN_ALERTS"
    )
    assert value is not None, "The TELEGRAM_API_TOKEN_ALERTS should not be None."
    assert isinstance(value, str), "The TELEGRAM_API_TOKEN_ALERTS should be a string."

    # Check for a non-existent key
    non_existent_value = src.handlers.load_variables_handler.get_json_key_value(
        "NON_EXISTENT_KEY"
    )
    assert non_existent_value is None, "The NON_EXISTENT_KEY should return None."


def test_get_int_variable():
    """
    Test the get_int_variable function from load_variables_handler.
    """
    print("Testing the get_int_variable function...")

    # Check if a known integer variable exists
    value = src.handlers.load_variables_handler.get_int_variable("ALERT_THRESHOLD_1H")
    assert value is not None, "The ALERT_THRESHOLD_1H should not be None."
    assert isinstance(value, int), "The ALERT_THRESHOLD_1H should be an integer."

    # Check for a non-existent key
    non_existent_value = src.handlers.load_variables_handler.get_int_variable(
        "NON_EXISTENT_INT_KEY", None
    )
    assert non_existent_value is None, "The NON_EXISTENT_INT_KEY should return None."


def test_save_transaction():
    """
    Test the save_transaction function from load_variables_handler.
    """
    print("Testing the save_transaction function...")

    test_file_path = "test_transaction.json"

    if os.path.exists(test_file_path):
        os.remove(test_file_path)

    # Save the transaction
    src.handlers.load_variables_handler.save_transaction(
        symbol="Test symbol",
        action="BUY",
        amount=100.0,
        price=50.0,
        file_path=test_file_path,
    )

    # Check if the transaction was saved correctly
    saved_transaction = src.handlers.load_variables_handler.load_transactions(
        test_file_path
    )

    assert len(saved_transaction) == 1, "There should be one transaction saved."
    assert (
        saved_transaction[0]["symbol"] == "Test symbol"
    ), "The saved transaction symbol should match."
    assert (
        saved_transaction[0]["action"] == "BUY"
    ), "The saved transaction action should be 'BUY'."
    assert (
        saved_transaction[0]["amount"] == 100.0
    ), "The saved transaction amount should be 100.0."
    assert (
        saved_transaction[0]["price"] == 50.0
    ), "The saved transaction price should be 50.0."


def test_load_keyword_list():
    """
    Test the load_keyword_list function from load_variables_handler.
    """
    print("Testing the load_keyword_list function...")

    # Load the keyword list
    keywords = src.handlers.load_variables_handler.load_keyword_list()

    # Check if the keywords are loaded correctly
    assert isinstance(keywords, list), "Keywords should be loaded as a list."
    assert len(keywords) > 0, "The keyword list should not be empty."
    assert all(
        isinstance(keyword, str) for keyword in keywords
    ), "All keywords should be strings."


def test_load_symbol_to_id():
    """
    Test the load_symbol_to_id function from load_variables_handler.
    """
    print("Testing the load_symbol_to_id function...")

    # Load the symbol to ID mapping
    symbol_to_id = src.handlers.load_variables_handler.load_symbol_to_id()

    # Check if the mapping is loaded correctly
    assert isinstance(
        symbol_to_id, dict
    ), "Symbol to ID mapping should be a dictionary."
    assert len(symbol_to_id) > 0, "The symbol to ID mapping should not be empty."
    assert all(
        isinstance(symbol, str) for symbol in symbol_to_id.keys()
    ), "All symbols should be strings."


def test_save_keyword():
    """
    Test the save_keyword function from load_variables_handler.
    """
    print("Testing the save_keyword function...")

    test_keyword = ["Test Keyword"]
    test_file_path = "test_keywords.json"

    if os.path.exists(test_file_path):
        os.remove(test_file_path)

    # Save the keyword
    src.handlers.load_variables_handler.save_keywords(test_keyword, test_file_path)

    # Load the keywords to check if the keyword was saved
    keywords = src.handlers.load_variables_handler.load_keyword_list(test_file_path)

    assert (
        test_keyword[0] in keywords
    ), f"The keyword '{test_keyword[0]}' should be saved in the keyword list."


def test_get_all_symbols():
    """
    Test the get_all_symbols function from load_variables_handler.
    """
    print("Testing the get_all_symbols function...")

    # Load all symbols
    symbols = src.handlers.load_variables_handler.get_all_symbols()

    # Check if the symbols are loaded correctly
    assert isinstance(symbols, list), "Symbols should be loaded as a list."
    assert len(symbols) == 0, "The symbol list should be empty."
