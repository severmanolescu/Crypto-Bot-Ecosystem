"""
CryptoRSICalculator: A Python module for calculating RSI (Relative Strength Index)
for cryptocurrency pairs using the Binance exchange API.
"""

# pylint: disable=broad-exception-caught, global-statement, too-many-locals

import logging
import os
import time
from multiprocessing import Pool

import ccxt
import numpy as np

logger = logging.getLogger(__name__)
logger.info("CryptoRSICalculator started")

# Module-level exchange instance for connection pooling
EXCHANGE_INSTANCE = None


def get_exchange():
    """
    Get or create a shared exchange instance
    Returns:
        ccxt.binance: An instance of the Binance exchange with rate limiting enabled.
    """
    global EXCHANGE_INSTANCE
    if EXCHANGE_INSTANCE is None:
        EXCHANGE_INSTANCE = ccxt.binance(
            {
                "enableRateLimit": True,  # Enable built-in rate limiting
            }
        )
    return EXCHANGE_INSTANCE


def calculate_rsi_for_symbol_batch(args):
    # pylint: disable=unused-variable
    """
    Process multiple symbols in a single process to reduce overhead
    Args:
        args (tuple): A tuple containing:
            - symbols (list): List of trading pair symbols to process.
            - timeframe (str): The timeframe for the OHLCV data.
            - rsi_period (int): The period for RSI calculation.
            - use_cache (bool): Whether to use cached OHLCV data.
    Returns:
        list: A list of tuples containing symbol and its RSI value.
    """
    symbols, timeframe, rsi_period, use_cache = args

    results = []

    exchange = ccxt.binance(
        {
            "enableRateLimit": True,
            "timeout": 10000,
        }
    )

    for symbol in symbols:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
            time.sleep(0.2)  # Small delay to avoid rate limits

            if not ohlcv or len(ohlcv) < rsi_period + 1:
                continue

            # Fast NumPy-based RSI calculation
            close_prices = np.array([candle[4] for candle in ohlcv])
            deltas = np.diff(close_prices)

            # Skip if not enough data
            if len(deltas) < rsi_period:
                continue

            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)

            # Use exponential moving average for RSI calculation
            avg_gain = np.zeros_like(deltas)
            avg_loss = np.zeros_like(deltas)

            # Initialize first values
            avg_gain[0] = np.mean(gains[:rsi_period])
            avg_loss[0] = np.mean(losses[:rsi_period])

            # Calculate smoothed averages
            for i in range(1, len(deltas)):
                avg_gain[i] = (
                    avg_gain[i - 1] * (rsi_period - 1) + gains[i]
                ) / rsi_period
                avg_loss[i] = (
                    avg_loss[i - 1] * (rsi_period - 1) + losses[i]
                ) / rsi_period

            rs = avg_gain / np.where(
                avg_loss != 0, avg_loss, 0.0001
            )  # Avoid division by zero
            rsi = 100 - (100 / (1 + rs))

            results.append((symbol, rsi[-1]))
        except Exception as e:
            logger.error("Error calculating RSI for %s: %s", symbol, str(e))

    return results


class CryptoRSICalculator:
    """
    CryptoRSICalculator: A class for calculating RSI (Relative Strength Index)
    """

    def __init__(self, rsi_period=14, load_markets=True):
        """
        Initialize the CryptoRSICalculator with a specified RSI period and optional market loading.
        Args:
            rsi_period (int): The period for RSI calculation (default is 14).
            load_markets (bool): Whether to load markets on initialization (default is True).
        """
        self.rsi_period = rsi_period
        self.exchange = get_exchange()
        self.tradable_pairs = []

        if load_markets:
            self._load_markets()

        # Cache for fetch operations
        self.ohlcv_cache = {}
        self.last_cache_clear = time.time()

    def _load_markets(self):
        """
        Load markets with retry logic
        """
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            logger.info(
                "Attempting to load markets from Binance (attempt %d)...",
                retry_count + 1,
            )
            try:
                markets = self.exchange.load_markets()
                logger.info("Successfully loaded %d markets", len(markets))

                # Filter for active USDT pairs only
                self.tradable_pairs = []

                # Pre-filter symbols to only include USDT pairs
                usdt_pairs = [symbol for symbol in markets if symbol.endswith("/USDT")]
                logger.info("Found %d USDT pairs in markets", len(usdt_pairs))

                # Process in batches to avoid slowdowns
                batch_size = 100
                for i in range(0, len(usdt_pairs), batch_size):
                    batch = usdt_pairs[i : i + batch_size]
                    for symbol in batch:
                        market_info = markets[symbol]
                        active_check = market_info.get("active", False)

                        if active_check:
                            self.tradable_pairs.append(symbol)

                logger.info(
                    "Found %d active USDT trading pairs", len(self.tradable_pairs)
                )
                return

            except Exception as e:
                retry_count += 1
                logger.error(
                    "Error loading markets (attempt %d): %s", retry_count, str(e)
                )

                if retry_count < max_retries:
                    wait_time = 2**retry_count  # Exponential backoff
                    logger.info("Retrying in %d seconds...", wait_time)

                    time.sleep(wait_time)
                else:
                    logger.error("Failed to load markets after multiple attempts")
                    self.tradable_pairs = []

    def fetch_ohlcv(self, symbol, timeframe="1h", limit=100, use_cache=True):
        """
        Fetch OHLCV data with optional caching
        Args:
            symbol (str): The trading pair symbol (e.g., 'BTC/USDT').
            timeframe (str): The timeframe for the OHLCV data (default is '1h').
            limit (int): The number of data points to fetch (default is 100).
            use_cache (bool): Whether to use cached data (default is True).
        Returns:
            list: List of OHLCV data for the given symbol and timeframe, or None if an error occurs.
        """
        # Clear cache periodically (every hour)
        current_time = time.time()
        if current_time - self.last_cache_clear > 3600:
            self.ohlcv_cache = {}
            self.last_cache_clear = current_time

        cache_key = f"{symbol}_{timeframe}_{limit}"

        cache_expiry = 600 if timeframe in ["1m", "5m", "15m"] else 3600

        if use_cache and cache_key in self.ohlcv_cache:
            cached_data, cache_time = self.ohlcv_cache[cache_key]
            if current_time - cache_time < cache_expiry:
                return cached_data

        try:
            data = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if use_cache:
                self.ohlcv_cache[cache_key] = (data, current_time)
            return data
        except Exception as e:
            logger.error("Error fetching OHLCV for %s: %s", symbol, str(e))
            return None

    def calculate_rsi(self, ohlcv):
        """Calculate RSI using numpy for better performance"""
        if not ohlcv or len(ohlcv) < self.rsi_period + 1:
            return None

        # Fast NumPy-based calculation
        close_prices = np.array([candle[4] for candle in ohlcv])
        deltas = np.diff(close_prices)

        # Skip if not enough data
        if len(deltas) < self.rsi_period:
            return None

        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.zeros_like(deltas)
        avg_loss = np.zeros_like(deltas)

        # Initialize first values
        avg_gain[0] = np.mean(gains[: self.rsi_period])
        avg_loss[0] = np.mean(losses[: self.rsi_period])

        # Calculate smoothed averages
        for i in range(1, len(deltas)):
            avg_gain[i] = (
                avg_gain[i - 1] * (self.rsi_period - 1) + gains[i]
            ) / self.rsi_period
            avg_loss[i] = (
                avg_loss[i - 1] * (self.rsi_period - 1) + losses[i]
            ) / self.rsi_period

        rs = avg_gain / np.where(
            avg_loss != 0, avg_loss, 0.0001
        )  # Avoid division by zero
        rsi = 100 - (100 / (1 + rs))

        return rsi[-1]

    def get_rsi_for_pairs(self, timeframe="1h", use_cache=True):
        """
        Get RSI for all pairs - now with batching to reduce overhead
        Args:
            timeframe (str): The timeframe for the OHLCV data (default is '1h').
            use_cache (bool): Whether to use cached OHLCV data (default is True).
        Returns:
            dict: A dictionary mapping trading pairs to their RSI values.
        """
        batch_size = 10  # Process in batches of 10 symbols
        rsi_values = {}

        for i in range(0, len(self.tradable_pairs), batch_size):
            batch = self.tradable_pairs[i : i + batch_size]
            for symbol in batch:
                try:
                    ohlcv = self.fetch_ohlcv(symbol, timeframe, use_cache=use_cache)
                    rsi = self.calculate_rsi(ohlcv)
                    if rsi is not None:
                        rsi_values[symbol] = rsi
                except Exception as e:
                    logger.error("Error fetching RSI for %s: %s", symbol, str(e))

            # Small sleep between batches to avoid rate limits
            if i + batch_size < len(self.tradable_pairs):
                time.sleep(0.1)

        return rsi_values

    def get_overbought_oversold_pairs(
        self, rsi_values, overbought_threshold=70, oversold_threshold=30
    ):
        """
        Find overbought and oversold pairs based on RSI values
        Args:
            rsi_values (dict): A dictionary mapping trading pairs to their RSI values.
            overbought_threshold (int): The threshold for overbought condition (default is 70).
            oversold_threshold (int): The threshold for oversold condition (default is 30).
        Returns:
            tuple: A tuple containing two lists:
                - overbought_pairs: List of tuples (symbol, rsi) for overbought pairs.
                - oversold_pairs: List of tuples (symbol, rsi) for oversold pairs.
        """
        overbought_pairs = []
        oversold_pairs = []

        for symbol, rsi in rsi_values.items():
            if rsi is not None:
                if rsi > overbought_threshold:
                    overbought_pairs.append((symbol, rsi))
                elif rsi < oversold_threshold:
                    oversold_pairs.append((symbol, rsi))

        return overbought_pairs, oversold_pairs

    def calculate_rsi_for_timeframes(
        self,
        timeframe="1h",
        overbought_threshold=70,
        oversold_threshold=30,
        use_cache=True,
    ):
        """
        Calculate RSI for all pairs - with better batching
        Args:
            timeframe (str): The timeframe for the OHLCV data (default is '1h').
            overbought_threshold (int): The threshold for overbought condition (default is 70).
            oversold_threshold (int): The threshold for oversold condition (default is 30).
            use_cache (bool): Whether to use cached OHLCV data (default is True).
        Returns:
            dict: A summary dictionary containing:
                - overbought: List of tuples (symbol, rsi) for overbought pairs.
                - oversold: List of tuples (symbol, rsi) for oversold pairs.
                - rsi_values: Dictionary mapping trading pairs to their RSI values.
        """
        pairs_to_process = self.tradable_pairs

        # Temporarily override tradable_pairs for processing
        original_pairs = self.tradable_pairs
        self.tradable_pairs = pairs_to_process

        rsi_values = self.get_rsi_for_pairs(timeframe, use_cache)

        # Restore original pairs
        self.tradable_pairs = original_pairs

        overbought_pairs, oversold_pairs = self.get_overbought_oversold_pairs(
            rsi_values, overbought_threshold, oversold_threshold
        )

        summary = {
            "overbought": overbought_pairs,
            "oversold": oversold_pairs,
            "rsi_values": rsi_values,
        }

        return summary

    def calculate_rsi_for_timeframes_parallel(
        self,
        timeframe="1h",
        use_cache=True,
    ):
        """
        Optimized multiprocessing version with improved performance
        Args:
            timeframe (str): The timeframe for the OHLCV data (default is '1h').
            use_cache (bool): Whether to use cached OHLCV data (default is True).
        Returns:
            dict: A summary dictionary containing:
                - overbought: List of tuples (symbol, rsi) for overbought pairs.
                - oversold: List of tuples (symbol, rsi) for oversold pairs.
                - rsi_values: Dictionary mapping trading pairs to their RSI values.
        """
        # Determine optimal process count based on system
        cpu_count = os.cpu_count()
        optimal_processes = max(
            2, min(cpu_count - 1, 8)
        )  # Between 2 and 8, leaving 1 core free

        logger.info("Using %d processes for RSI calculation", optimal_processes)

        # Split symbols into roughly equal chunks for each process
        symbols = self.tradable_pairs

        # If very few symbols, just use one process
        if len(symbols) < 10:
            optimal_processes = 1

        chunk_size = max(5, len(symbols) // optimal_processes)
        symbol_chunks = [
            symbols[i : i + chunk_size] for i in range(0, len(symbols), chunk_size)
        ]

        # Prepare arguments for each process
        args_list = [
            (chunk, timeframe, self.rsi_period, use_cache) for chunk in symbol_chunks
        ]

        logger.info("Starting multiprocessing pool")
        with Pool(processes=optimal_processes) as pool:
            nested_results = pool.map(calculate_rsi_for_symbol_batch, args_list)

        logger.info("Finished multiprocessing pool")

        # Flatten results
        all_results = [item for sublist in nested_results for item in sublist]

        # Convert to dictionary
        rsi_values = {symbol: rsi for symbol, rsi in all_results if rsi is not None}

        return {
            "values": rsi_values,
        }
