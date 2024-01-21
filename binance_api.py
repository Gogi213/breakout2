# binance_api.py
import requests
import pandas as pd
from cache_manager import CacheManager

cache_manager = CacheManager()

def get_top_futures_pairs(base_currency='USDT', volume_threshold=80000000):
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Error fetching data from Binance Futures API")

    data = response.json()
    pairs = [item for item in data if item['symbol'].endswith(base_currency) and float(item['quoteVolume']) >= volume_threshold]
    pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
    return [pair['symbol'] for pair in pairs]


def calculate_natr(df, period=7):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()

    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(window=period).mean()

    # Нормализация ATR (преобразование в nATR)
    natr = (atr / df['Close'])

    return natr

def get_historical_futures_data(symbol, interval='15m', limit=1500):
    cached_data = cache_manager.load_cache(symbol, interval)
    if cached_data is not None:
        return cached_data

    url = f"https://fapi.binance.com/fapi/v1/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data for {symbol}")

    data = response.json()
    df = pd.DataFrame(data, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
    df['symbol'] = symbol  # Добавляем колонку 'symbol'
    # Преобразование времени и числовых данных
    df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')

    df['Close time'] = pd.to_datetime(df['Close time'], unit='ms')

    numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Расчет и добавление nATR
    df['nATR'] = calculate_natr(df)

    cache_manager.save_cache(df, symbol, interval)
    df.set_index('Open time', inplace=True)
    return df

def preload_data():
    top_pairs = get_top_futures_pairs()
    for pair in top_pairs:
        get_historical_futures_data(pair)

# Дополнительные функции и логика (если необходимо)