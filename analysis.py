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
        start_idx = df.index.get_loc(pair[0][0])
        end_idx = df.index.get_loc(pair[1][0])

        # Проверяем, что вершина и тест не на одной свече и расстояние между ними >= 15
        if start_idx != end_idx and end_idx - start_idx >= 15:
            peak_price = pair[0][1]
            test_price = pair[1][1]

            # Дополнительные проверки
            if test_price <= peak_price and all(df['High'][i] <= peak_price for i in range(start_idx + 1, end_idx)):
                valid_pairs.append(pair)

    return valid_pairs

def validate_low_setup(df, pairs):
    valid_pairs = []
    for pair in pairs:
        start_idx = df.index.get_loc(pair[0][0])
        end_idx = df.index.get_loc(pair[1][0])

        # Проверяем, что дно и тест не на одной свече и расстояние между ними >= 15
        if start_idx != end_idx and end_idx - start_idx >= 15:
            bottom_price = pair[0][1]
            test_price = pair[1][1]

            # Дополнительные проверки
            if test_price >= bottom_price and all(df['Low'][i] >= bottom_price for i in range(start_idx + 1, end_idx)):
                valid_pairs.append(pair)

    return valid_pairs

def find_breakout_candles(df, pairs, is_high=True):
    breakout_candles = []

    for pair in pairs:
        peak_idx, peak_price = pair[0]
        test_idx, test_price = pair[1]

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

def emulate_position_tracking(df, breakout_candles):
    results = []

    for pair, breakout_idx in breakout_candles:
        test_idx, test_price = pair[1]
        nATR = df.at[breakout_idx, 'nATR']
        tp_price = test_price + test_price * nATR
        sl_price = test_price - test_price * nATR / 2

        position_opened = False
        position_outcome = None

        # Перебор свечей после пробоя для определения TP или SL
        for i in range(breakout_idx, len(df)):
            candle = df.iloc[i]
            if candle['High'] >= tp_price:
                position_outcome = 'TP'
                break
            elif candle['Low'] <= sl_price:
                position_outcome = 'SL'
                break

        # Добавляем результаты в список
        if position_outcome == 'TP':
            results.append((pair, 'Successful', nATR))
        elif position_outcome == 'SL':
            results.append((pair, 'Unsuccessful', nATR / 2))

    return results
