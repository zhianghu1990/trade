import yfinance as yf
import pandas as pd

def get_etf_prices(ticker_symbol):
    """
    Fetches the current price and historical high for a given ETF ticker.
    """
    try:
        # Create a Ticker object for the ETF
        etf_ticker = yf.Ticker(ticker_symbol)

        # Method 1: Get data from the 'info' dictionary for the most recent price
        # 'currentPrice' or 'regularMarketPrice' are options
        current_price = etf_ticker.info.get('currentPrice')
        
        # Method 2: Download the entire history to find the all-time high
        # period='max' fetches all available historical data
        hist_data = etf_ticker.history(period="max")
        
        if hist_data.empty:
            print(f"No historical data found for {ticker_symbol}.")
            return None, None
            
        historical_high = hist_data['High'].max()

        if current_price is None:
            # Fallback to the last available closing price if 'currentPrice' is not available
            current_price = hist_data['Close'].iloc[-1]
            print(f"Warning: 'currentPrice' not found, using last close price: {current_price}")

        return current_price, historical_high

    except Exception as e:
        print(f"An error occurred while fetching data for {ticker_symbol}: {e}")
        return None, None

# Specify the ETF ticker
etf_ticker_symbol = "VOO"
# TODO: update to symbol + threshold.

# Get the prices
current_price_voo, historical_high_voo = get_etf_prices(etf_ticker_symbol)

# Print the results
# TODO email results (and when necessary).
if current_price_voo is not None and historical_high_voo is not None:
    print(f"Current price for {etf_ticker_symbol}: ${current_price_voo:.2f}")
    print(f"Historical high for {etf_ticker_symbol}: ${historical_high_voo:.2f}")
    
    # Calculate the 95% threshold
    threshold = historical_high_voo * 0.95
    print(f"95% of historical high: ${threshold:.2f}")

    if current_price_voo < threshold:
        print(f"\nALERT: VOO's price is below 95% of its historical high!")
    else:
        print("\nVOO's price is above the 95% threshold.")

