# analysis.py
import pandas as pd

# Функции для расчета точек разворота
def find_pivot_high(df, left_bars, right_bars):
    highs = []
    for i in range(left_bars, len(df) - right_bars):
        if df['High'][i] == max(df['High'][i-left_bars:i+right_bars+1]):
            highs.append((df.index[i], df['High'][i]))
        else:
            highs.append((df.index[i], None))
    return highs

def find_pivot_low(df, left_bars, right_bars):
    lows = []
    for i in range(left_bars, len(df) - right_bars):
        if df['Low'][i] == min(df['Low'][i-left_bars:i+right_bars+1]):
            lows.append((df.index[i], df['Low'][i]))
        else:
            lows.append((df.index[i], None))
    return lows

# Функция для поиска пар точек
# analysis.py

def find_pairs(pivot_highs, df):
    pairs = []
    for i in range(len(pivot_highs)):
        high_idx, high_price = pivot_highs[i]
        if high_price is not None:
            current_nATR = df.at[high_idx, 'nATR']
            if pd.notna(current_nATR):
                threshold = current_nATR / 2
                for j in range(i+1, len(pivot_highs)):
                    _, next_high_price = pivot_highs[j]
                    if next_high_price is not None:
                        price_diff = abs(next_high_price - high_price) / high_price
                        if pd.notna(price_diff) and price_diff <= threshold:
                            pairs.append((pivot_highs[i], pivot_highs[j]))
    return pairs


def find_low_pairs(pivot_lows, df):
    pairs = []
    for i in range(len(pivot_lows)):
        low_idx, low_price = pivot_lows[i]
        if low_price is not None:
            # Убедимся, что nATR является числом
            current_nATR = df.at[low_idx, 'nATR']
            if pd.notna(current_nATR):
                threshold = current_nATR / 2
                for j in range(i+1, len(pivot_lows)):
                    _, next_low_price = pivot_lows[j]
                    if next_low_price is not None:
                        price_diff = abs(next_low_price - low_price) / low_price
                        # Убедимся, что price_diff является числом
                        if pd.notna(price_diff) and price_diff <= threshold:
                            pairs.append((pivot_lows[i], pivot_lows[j]))
    return pairs


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

def validate_low_setup(df, pairs):
    valid_pairs = []
    for pair in pairs:
        is_valid = True
        start_idx = df.index.get_loc(pair[0][0])
        end_idx = df.index.get_loc(pair[1][0])

        # Цена дна
        bottom_price = pair[0][1]
        # Цена теста
        test_price = pair[1][1]

        # Проверяем, что цена теста не ниже и не равна цене дна
        if test_price < bottom_price:
            is_valid = False

        # Проверяем, что свечи между тестами и дном не ниже дна
        for i in range(start_idx + 1, end_idx):
            if df['Low'][i] < bottom_price:
                is_valid = False
                break

        if is_valid:
            valid_pairs.append(pair)

    return valid_pairs

def validate_breakout_setups(df, valid_high_pairs, nATR_column='nATR'):
    successful_breakouts = 0
    unsuccessful_breakouts = 0
    sum_nATR_successful = 0
    sum_nATR_unsuccessful = 0

    for pair in valid_high_pairs:
        peak_idx, peak_price = pair[0]
        test_idx, test_price = pair[1]

        # Исключаем открытые сетапы
        if test_idx >= len(df) - 1:
            continue

        # Находим свечу, которая пробивает уровень верхнего сетапа
        breakout_candle_idx = df.index.get_loc(test_idx) + 1
        breakout_candle = df.iloc[breakout_candle_idx]

        # Условия для оценки пробоя
        nATR_value = df.at[test_idx, nATR_column]
        upper_bound = test_price + nATR_value
        lower_bound = test_price - nATR_value / 2

        if breakout_candle['High'] >= upper_bound:
            # Успешный пробой
            successful_breakouts += 1
            sum_nATR_successful += nATR_value
        elif test_price < breakout_candle['High'] < upper_bound or breakout_candle['Low'] <= lower_bound:
            # Неуспешный пробой
            unsuccessful_breakouts += 1
            sum_nATR_unsuccessful += nATR_value / 2

    breakout_stats = {
        'successful_breakouts': successful_breakouts,
        'unsuccessful_breakouts': unsuccessful_breakouts,
        'success_rate': successful_breakouts / (successful_breakouts + unsuccessful_breakouts) if successful_breakouts + unsuccessful_breakouts > 0 else 0,
        'sum_nATR_successful': sum_nATR_successful,
        'sum_nATR_unsuccessful': sum_nATR_unsuccessful
    }

    return breakout_stats
