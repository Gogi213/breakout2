import pandas as pd
from binance_api import get_historical_futures_data
import plot

# Функции для расчета точек разворота
def find_pivot_high(df, left_bars, right_bars):
    highs = []
    for i in range(left_bars, len(df) - right_bars):
        if df['High'][i] == max(df['High'][i-left_bars:i+right_bars+1]):
            highs.append((df.index[i], df['High'][i]))
        else:
            highs.append((df.index[i], None))
    return highs

# Функция для расчета осциллятора объема
def calculate_volume_oscillator(df):
    short_ema = df['Volume'].ewm(span=5, adjust=False).mean()
    long_ema = df['Volume'].ewm(span=10, adjust=False).mean()
    df['volume_osc'] = 100 * (short_ema - long_ema) / long_ema

# Функция для поиска пар точек
def find_pairs(pivot_highs, threshold=0.0015):
    pairs = []
    for i in range(len(pivot_highs)):
        for j in range(i+1, len(pivot_highs)):
            if pivot_highs[i][1] and pivot_highs[j][1]:
                if pivot_highs[j][0] > pivot_highs[i][0]:
                    price_diff = abs(pivot_highs[j][1] - pivot_highs[i][1]) / pivot_highs[i][1]
                    if price_diff <= threshold:
                        pairs.append((pivot_highs[i], pivot_highs[j]))
    return pairs

# Функция для проверки валидности сетапа
# Функция для проверки валидности сетапа
def validate_setup(df, pairs):
    valid_pairs = []
    for pair in pairs:
        is_valid = True
        start_idx = df.index.get_loc(pair[0][0])
        end_idx = df.index.get_loc(pair[1][0])

        # Цена вершины
        peak_price = pair[0][1]
        # Цена теста
        test_price = pair[1][1]

        # Проверяем, что цена теста не выше и не равна цене вершины
        if test_price > peak_price:
            is_valid = False

        # Проверяем, что свечи между тестами и вершиной не выше вершины
        for i in range(start_idx + 1, end_idx):
            if df['High'][i] > peak_price:
                is_valid = False
                break

        if is_valid:
            valid_pairs.append(pair)

    return valid_pairs


# Основной код
def main():
    symbol = 'btcusdt'  # Замените на ваш торговый символ
    df = get_historical_futures_data(symbol)

    pivot_highs = find_pivot_high(df, left_bars=10, right_bars=10)
    calculate_volume_oscillator(df)
    pairs = find_pairs(pivot_highs)
    valid_pairs = validate_setup(df, pairs)
    plot.plot_support_resistance_with_annotations(df, valid_pairs)

if __name__ == "__main__":
    main()