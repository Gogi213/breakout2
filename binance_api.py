# binance_api.py
import requests
import pandas as pd
from cache_manager import CacheManager
import datetime

cache_manager = CacheManager()

def get_top_futures_pairs(base_currency='USDT', volume_threshold=200000000):
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

def get_historical_futures_data(symbol, interval='5m', limit=1500, batches=3):
    cached_data = cache_manager.load_cache(symbol, interval)
    if cached_data is not None:
        return cached_data

    all_data = pd.DataFrame()
    end_time = None

    for _ in range(batches):
        url = f"https://fapi.binance.com/fapi/v1/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit,
            'endTime': end_time  # Используем endTime для смещения запроса
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching data for {symbol}")

        data = response.json()
        df = pd.DataFrame(data, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
        df['symbol'] = symbol

        if df.empty:
            print(f"Нет данных для {symbol} в запросе, пропускаем этот пакет")
            continue

        # Преобразование времени и числовых данных
        df['Open time'] = pd.to_datetime(df['Open time'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('EET')
        df['Close time'] = pd.to_datetime(df['Close time'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('EET')
        df['Formatted Open Time'] = df['Open time'].dt.strftime('%Y-%m-%d %H:%M')

        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Расчет и добавление nATR
        df['nATR'] = calculate_natr(df)

        # Объединяем данные
        all_data = pd.concat([all_data, df])

        # Обновляем endTime для следующего запроса
        end_time = int(df['Open time'].iloc[0].timestamp() * 1000) - 1

    if all_data.empty:
        print(f"Нет данных для {symbol} после {batches} запросов")
        return None

    # Удаление дубликатов
    all_data.drop_duplicates(subset=['Open time'], inplace=True)

    # Сортировка данных по времени
    all_data.sort_values(by='Open time', inplace=True)

    # Сохраняем в кеш
    cache_manager.save_cache(all_data, symbol, interval)
    all_data.set_index('Open time', inplace=True)
    return all_data



def preload_data():
    top_pairs = get_top_futures_pairs()
    for pair in top_pairs:
        get_historical_futures_data(pair)

# Дополнительные функции и логика (если необходимо)