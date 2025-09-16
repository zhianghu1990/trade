import yfinance as yf
import pandas as pd
import os
import requests
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
import datetime
import pandas_market_calendars as mcal
from datetime import timezone


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

def send_message(subject,text):
  return requests.post(
    "https://api.mailgun.net/v3/sandboxe8cddc1d54854e26a7aba3550e8daa0d.mailgun.org/messages",
    auth=("api", os.getenv('API_KEY', '2b13d4fd874e1bf7f8b78ade03fbe62f-3c134029-19ae4db8')),
    data={"from": "Mailgun Sandbox <postmaster@sandboxe8cddc1d54854e26a7aba3550e8daa0d.mailgun.org>",
    "to": "Harvey H <hza8816415@gmail.com>",
      "subject": subject,
      "text": text})

def send_alerts(tickers,alerts):
  subject = "Watch out"
  text = ""
  for ticker in tickers:
    subject = subject + " " + ticker
  for alert in alerts:
    drop_pct = (1.0 - alert[1] / alert[2]) * 100
    text = text + f"{alert[0]}: Current Price: ${alert[1]:.2f} Historical High: {alert[2]:.2f}, dropped {drop_pct:.2f}%, which is below threshold {alert[3]*100:.2f}%. \n"
  return send_message(subject,text)

def compare_current_with_high(etf_ticker_symbol, threshold):
    current_price, historical_high = get_etf_prices(etf_ticker_symbol)
    if current_price is not None and historical_high is not None:
      if current_price < threshold * historical_high:
        return True, current_price, historical_high
    return False, current_price, historical_high


def is_trading_day():
    """
    Checks if today is a trading day (market open) in the US.
    """
    # Define US trading days (weekdays excluding US federal holidays)
    us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())

    # Get today's date
    today = datetime.date.today()

    # Check if today is a business day according to the US trading calendar
    return bool(len(pd.date_range(start=today, end=today, freq=us_bd)))

def is_last_trading_day_of_month(market='NYSE'):
    """
    Checks if today is the last trading day of the month for the specified market.
    """
    today = datetime.date.today()
    
    # Get the calendar for the specified market
    calendar = mcal.get_calendar(market)
    
    # Get all trading days for the current month
    # We need to specify a range that definitely includes the whole month
    start_of_month = today.replace(day=1)
    # Go slightly into next month to ensure we catch the last day
    end_of_month = (start_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    
    schedule = calendar.schedule(start_date=start_of_month, end_date=end_of_month)
    
    if schedule.empty:
        return False, None # No trading days found in the month
        
    # Get the last trading day from the schedule
    last_trading_day_of_month = schedule.index[-1].date()
    
    print(f"Today: {today}, Last Trading Day of Month ({market}): {last_trading_day_of_month}")

    current_utc_time = datetime.datetime.now(timezone.utc)
    # runs 13 - 20:00 UTC, aka 7am - 14:00 PT.
    target_utc_hour = 14 # 14 AM UTC 7 AM PT
    force_start_utc_hour = 6 # 0 - 6 am UTC, 17 - 23 PM PST yesterday.
    
    return (
        (today == last_trading_day_of_month and current_utc_time.hour < target_utc_hour)
        or current_utc_time.hour < force_start_utc_hour)
    
symbols = ["VOO", "VGT", "MGK"]
thresholds = [0.95, 0.9483, 0.9407]
should_send = False
tickers = []
alerts = []
currents = []
highs = []

if is_trading_day():
    for i in range(len(symbols)):
      result, current, hist_high = compare_current_with_high(symbols[i], thresholds[i])
      currents.append(current)
      highs.append(hist_high)
      if result:
        should_send = True
        tickers.append(symbols[i])
        alerts.append((symbols[i], current, hist_high, thresholds[i]))
    
    if should_send:
      send_alerts(tickers,alerts)
    elif is_last_trading_day_of_month():
        subject = "Monthly Summary " + str(datetime.date.today())
        text = ""
        for i in range(len(symbols)):
            diff_now = (1.0 - currents[i] / highs[i]) * 100
            text = text + symbols[i] + f" Current price ${currents[i]:.2f} historical high ${highs[i]:.2f}. drop {diff_now:.2f}%\n"
        send_message(subject,text)
