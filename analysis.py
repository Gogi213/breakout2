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

def find_multi_test_pairs(pivot_highs, df):
    multi_test_pairs = []
    for i in range(len(pivot_highs)):
        high_idx, high_price = pivot_highs[i]
        if high_price is None:
            continue

        current_nATR = df.at[high_idx, 'nATR']
        if pd.notna(current_nATR):
            threshold = current_nATR / 2
            tests = []
            for j in range(i+1, len(pivot_highs)):
                _, next_high_price = pivot_highs[j]
                if next_high_price is None:
                    continue

                price_diff = abs(next_high_price - high_price) / high_price
                if pd.notna(price_diff) and price_diff <= threshold:
                    if not tests or next_high_price <= tests[-1][1]:  # Убедимся, что каждый следующий тест ниже или равен предыдущему
                        tests.append(pivot_highs[j])

            if tests:
                multi_test_pairs.append((pivot_highs[i], tests))
    print("multi test pairs -", multi_test_pairs)
    return multi_test_pairs


def find_low_pairs(pivot_lows, df):
    low_pairs = []
    for i in range(len(pivot_lows)):
        low_idx, low_price = pivot_lows[i]
        if low_price is None:
            continue

        current_nATR = df.at[low_idx, 'nATR']
        if pd.notna(current_nATR):
            threshold = current_nATR / 2
            tests = []
            for j in range(i+1, len(pivot_lows)):
                _, next_low_price = pivot_lows[j]
                if next_low_price is None:
                    continue

                price_diff = abs(next_low_price - low_price) / low_price
                if pd.notna(price_diff) and price_diff <= threshold:
                    if not tests or next_low_price >= tests[-1][1]:  # Для нижних вершин
                        tests.append(pivot_lows[j])

            if tests:
                low_pairs.append((pivot_lows[i], tests))
    print("Low pairs -", low_pairs)
    return low_pairs


# Функция для проверки валидности сетапа
def validate_setup(df, pairs):
    valid_pairs = []
    for pair in pairs:
        main_peak = pair[0]
        tests = pair[1]
        valid_tests = []
        for test in tests:
            start_idx = df.index.get_loc(main_peak[0])
            end_idx = df.index.get_loc(test[0])

            if start_idx != end_idx and end_idx - start_idx >= 15:
                peak_price = main_peak[1]
                test_price = test[1]

                if test_price <= peak_price and all(df['High'][i] <= peak_price for i in range(start_idx + 1, end_idx)):
                    valid_tests.append(test)

        if valid_tests:
            valid_pairs.append((main_peak, valid_tests))
    print("valid_pairs -", valid_pairs)
    return valid_pairs


def validate_low_setup(df, pairs):
    valid_pairs = []
    for pair in pairs:
        main_low = pair[0]
        tests = pair[1]
        valid_tests = []
        for test in tests:
            start_idx = df.index.get_loc(main_low[0])
            end_idx = df.index.get_loc(test[0])

            if start_idx != end_idx and end_idx - start_idx >= 15:
                low_price = main_low[1]
                test_price = test[1]

                if test_price >= low_price and all(df['Low'][i] >= low_price for i in range(start_idx + 1, end_idx)):
                    valid_tests.append(test)

        if valid_tests:
            valid_pairs.append((main_low, valid_tests))
    print("Low valid_pairs -", valid_pairs)
    return valid_pairs

def find_breakout_candles(df, pairs, is_high=True):
    breakout_candles = []

    for pair in pairs:
        peak_idx, peak_price = pair[0]
        tests = pair[1]

        for test in tests:
            test_idx, test_price = test

            # Исключаем открытые сетапы
            if test_idx >= len(df) - 1:
                continue

            # Перебираем свечи после теста для поиска пробоя
            for i in range(test_idx + 1, len(df)):
                candle = df.iloc[i]
                if is_high:
                    # Для верхних сетапов: пробой снизу вверх
                    if candle['Low'] <= test_price and candle['High'] >= test_price:
                        breakout_candles.append((pair, i))
                        break
                else:
                    # Для нижних сетапов: пробой сверху вниз
                    if candle['High'] >= test_price and candle['Low'] <= test_price:
                        breakout_candles.append((pair, i))
                        break

    return breakout_candles


def emulate_position_tracking(df, breakout_candles, nATR_column='nATR'):
    results = []

    for pair, breakout_idx in breakout_candles:
        test_price = pair[1][1]  # Цена нижнего теста
        nATR_value = df.at[breakout_idx, nATR_column]

        tp = test_price + test_price * nATR_value
        sl = test_price - test_price * (nATR_value / 2)

        outcome = None
        profit_loss = 0

        # Перебор свечей после пробоя для определения TP или SL
        for i in range(breakout_idx + 1, len(df)):
            high_price = df.at[i, 'High']
            low_price = df.at[i, 'Low']

            if high_price >= tp:
                outcome = 'Successful'
                profit_loss = nATR_value * 100
                break
            elif low_price <= sl:
                outcome = 'Unsuccessful'
                profit_loss = (-nATR_value / 2) * 100
                break

        results.append({
            'setup': pair,
            'breakout_idx': breakout_idx,
            'outcome': outcome,
            'profit_loss': profit_loss
        })

    return results