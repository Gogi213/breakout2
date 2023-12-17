# cache_manager.py
import pandas as pd
import os
import json

class CacheManager:
    def __init__(self, cache_dir='cache'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def _get_cache_file_path(self, symbol, interval):
        return os.path.join(self.cache_dir, f"{symbol}_{interval}.json")

    def load_cache(self, symbol, interval):
        cache_file = self._get_cache_file_path(symbol, interval)
        if os.path.exists(cache_file) and os.path.getsize(cache_file) > 0:
            with open(cache_file, 'r') as file:
                try:
                    data = json.load(file)
                    return pd.DataFrame(data)
                except json.JSONDecodeError:
                    print(f"Ошибка чтения файла кеша: {cache_file}")
                    return None
        return None

    def save_cache(self, df, symbol, interval):
        # Преобразование Timestamp в строку
        df['Open time'] = df['Open time'].astype(str)
        df['Close time'] = df['Close time'].astype(str)

        cache_file = self._get_cache_file_path(symbol, interval)
        with open(cache_file, 'w') as file:
            json.dump(df.to_dict('records'), file)