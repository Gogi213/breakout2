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
    used_tests = set()  # Множество для хранения индексов использованных тестов

    for i in range(len(pivot_highs)):
        high_idx, high_price = pivot_highs[i]
        if high_price is not None:
            current_nATR = df.at[high_idx, 'nATR']
            if pd.notna(current_nATR):
                threshold = current_nATR / 2
                best_test = None
                for j in range(i + 1, len(pivot_highs)):
                    next_idx, next_high_price = pivot_highs[j]
                    if next_high_price is not None and next_idx not in used_tests:
                        price_diff = abs(next_high_price - high_price) / high_price
                        if pd.notna(price_diff) and price_diff <= threshold:
                            if best_test is None or (next_high_price > best_test[1] and next_high_price <= high_price):
                                best_test = (next_idx, next_high_price)
                if best_test:
                    pairs.append((pivot_highs[i], best_test))
                    # Помечаем все последующие точки в пределах threshold как использованные
                    for k in range(best_test[0], min(best_test[0] + int(threshold), len(pivot_highs))):
                        used_tests.add(pivot_highs[k][0])
    return pairs



def find_low_pairs(pivot_lows, df):
    pairs = []
    used_tests = set()  # Множество для хранения индексов использованных тестов

    for i in range(len(pivot_lows)):
        low_idx, low_price = pivot_lows[i]
        if low_price is not None:
            current_nATR = df.at[low_idx, 'nATR']
            if pd.notna(current_nATR):
                threshold = current_nATR / 2
                best_test = None
                for j in range(i + 1, len(pivot_lows)):
                    next_idx, next_low_price = pivot_lows[j]
                    if next_low_price is not None and next_idx not in used_tests:
                        price_diff = abs(next_low_price - low_price) / low_price
                        if pd.notna(price_diff) and price_diff <= threshold:
                            if best_test is None or (next_low_price < best_test[1] and next_low_price >= low_price):
                                best_test = (next_idx, next_low_price)
                if best_test:
                    pairs.append((pivot_lows[i], best_test))
                    # Помечаем все последующие точки в пределах threshold как использованные
                    for k in range(best_test[0], min(best_test[0] + int(threshold), len(pivot_lows))):
                        used_tests.add(pivot_lows[k][0])
    return pairs



# Функция для проверки валидности сетапа
def validate_setup(df, pairs):
    valid_pairs = []
    used_breakout_candles = set()

    for pair in pairs:
        start_idx = df.index.get_loc(pair[0][0])
        end_idx = df.index.get_loc(pair[1][0])

        # Проверка на пересечение сетапов более чем на одну свечу
        if any(start_idx <= other_end_idx and end_idx >= other_start_idx
               for other_start_idx, other_end_idx in valid_pairs):
            continue

        # Проверка на использование одной и той же пробойной свечи
        if end_idx in used_breakout_candles:
            continue

        # Дополнительные проверки и добавление валидных пар
        if start_idx != end_idx and end_idx - start_idx >= 15:
            peak_price = pair[0][1]
            test_price = pair[1][1]
            if test_price <= peak_price and all(df['High'][i] <= peak_price for i in range(start_idx + 1, end_idx)):
                valid_pairs.append((start_idx, end_idx))
                used_breakout_candles.add(end_idx)

    return [pair for pair in pairs if (df.index.get_loc(pair[0][0]), df.index.get_loc(pair[1][0])) in valid_pairs]


def validate_low_setup(df, pairs):
    valid_pairs = []
    used_breakout_candles = set()

    for pair in pairs:
        start_idx = df.index.get_loc(pair[0][0])
        end_idx = df.index.get_loc(pair[1][0])

        # Проверка на пересечение сетапов более чем на одну свечу
        if any(start_idx <= other_end_idx and end_idx >= other_start_idx
               for other_start_idx, other_end_idx in valid_pairs):
            continue

        # Проверка на использование одной и той же пробойной свечи
        if end_idx in used_breakout_candles:
            continue

        # Дополнительные проверки и добавление валидных пар
        if start_idx != end_idx and end_idx - start_idx >= 15:
            bottom_price = pair[0][1]
            test_price = pair[1][1]
            if test_price >= bottom_price and all(df['Low'][i] >= bottom_price for i in range(start_idx + 1, end_idx)):
                valid_pairs.append((start_idx, end_idx))
                used_breakout_candles.add(end_idx)

    return [pair for pair in pairs if (df.index.get_loc(pair[0][0]), df.index.get_loc(pair[1][0])) in valid_pairs]

def find_breakout_candles(df, pairs, is_high=True, min_candles_after_test=5):
    breakout_candles = []

    for pair in pairs:
        peak_idx, peak_price = pair[0]
        test_idx, test_price = pair[1]

        # Исключаем открытые сетапы
        if test_idx >= len(df) - 1:
            continue

        # Перебираем свечи после теста для поиска пробоя
        for i in range(test_idx + 1, len(df)):
            # Проверяем, что пробойная свеча не ближе чем на 5 свечей к тесту
            if i - test_idx < min_candles_after_test:
                continue

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