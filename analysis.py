# analysis.py
import pandas as pd

# Функции для расчета точек разворота
def find_pivot_high(df, left_bars, right_bars):
    highs = []
    for i in range(left_bars, len(df) - right_bars):
        window = df.iloc[i-left_bars:i+right_bars+1]
        if df['High'].iloc[i] == max(window['High']):
            highs.append((df.index[i], df['High'].iloc[i]))
        else:
            highs.append((df.index[i], None))
    return highs

def find_pivot_low(df, left_bars, right_bars):
    lows = []
    for i in range(left_bars, len(df) - right_bars):
        window = df.iloc[i-left_bars:i+right_bars+1]
        if df['Low'].iloc[i] == min(window['Low']):
            lows.append((df.index[i], df['Low'].iloc[i]))
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
    for i in range(len(pairs) - 1):
        current_pair = pairs[i]
        next_pair = pairs[i + 1]

        start_idx = df.index.get_loc(current_pair[0][0])
        end_idx = df.index.get_loc(current_pair[1][0])

        if start_idx != end_idx and end_idx - start_idx >= 30:
            peak_price = current_pair[0][1]
            test_price = current_pair[1][1]

            if test_price <= peak_price and all(df['High'][j] <= peak_price for j in range(start_idx + 1, end_idx)):
                # Дополнительное условие: проверяем, что тест текущей пары не является вершиной следующей пары
                if current_pair[1][0] != next_pair[0][0]:
                    valid_pairs.append(current_pair)

    # Проверяем последнюю пару отдельно, так как она не может быть продолжением следующей
    if len(pairs) > 0:
        last_pair = pairs[-1]
        start_idx = df.index.get_loc(last_pair[0][0])
        end_idx = df.index.get_loc(last_pair[1][0])

        if start_idx != end_idx and end_idx - start_idx >= 30:
            peak_price = last_pair[0][1]
            test_price = last_pair[1][1]

            if test_price <= peak_price and all(df['High'][j] <= peak_price for j in range(start_idx + 1, end_idx)):
                valid_pairs.append(last_pair)

    return valid_pairs


def validate_low_setup(df, pairs):
    valid_pairs = []
    for i in range(len(pairs) - 1):
        current_pair = pairs[i]
        next_pair = pairs[i + 1]

        start_idx = df.index.get_loc(current_pair[0][0])
        end_idx = df.index.get_loc(current_pair[1][0])

        if start_idx != end_idx and end_idx - start_idx >= 30:
            bottom_price = current_pair[0][1]
            test_price = current_pair[1][1]

            if test_price >= bottom_price and all(df['Low'][j] >= bottom_price for j in range(start_idx + 1, end_idx)):
                # Дополнительное условие: проверяем, что тест текущей пары не является дном следующей пары
                if current_pair[1][0] != next_pair[0][0]:
                    valid_pairs.append(current_pair)

    # Проверяем последнюю пару отдельно, так как она не может быть продолжением следующей
    if len(pairs) > 0:
        last_pair = pairs[-1]
        start_idx = df.index.get_loc(last_pair[0][0])
        end_idx = df.index.get_loc(last_pair[1][0])

        if start_idx != end_idx and end_idx - start_idx >= 30:
            bottom_price = last_pair[0][1]
            test_price = last_pair[1][1]

            if test_price >= bottom_price and all(df['Low'][j] >= bottom_price for j in range(start_idx + 1, end_idx)):
                valid_pairs.append(last_pair)

    return valid_pairs


def find_breakout_candles(df, pairs, is_high=True, min_candles_after_test=5):
    breakout_candles = []
    # Добавляем словарь для отслеживания breakout по numbers
    breakout_by_numbers = {}

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
                    # Проверяем, не принадлежит ли этот breakout уже другому numbers
                    if i not in breakout_by_numbers or df.index.get_loc(pair[0][0]) < df.index.get_loc(breakout_by_numbers[i][0][0]):
                        breakout_candles.append((pair, i))
                        breakout_by_numbers[i] = pair
                    break
            else:
                # Для нижних сетапов: пробой сверху вниз
                if candle['High'] >= test_price and candle['Low'] <= test_price:
                    # Аналогичная проверка для нижних сетапов
                    if i not in breakout_by_numbers or df.index.get_loc(pair[0][0]) < df.index.get_loc(breakout_by_numbers[i][0][0]):
                        breakout_candles.append((pair, i))
                        breakout_by_numbers[i] = pair
                    break

    return breakout_candles


def emulate_position_tracking(df, breakout_candles, initial_deposit=100, leverage=6, limit_commission=0.0002, market_commission=0.00055):
    results = []
    balance = initial_deposit

    for pair, breakout_idx in breakout_candles:
        test_price = pair[1][1]
        nATR_value = df.at[breakout_idx, 'nATR']

        tp = test_price + (test_price * nATR_value * 1.5)
        sl = test_price - test_price * (nATR_value / 1.8)

        # Расчет комиссии при входе
        entry_commission = balance * limit_commission
        balance -= entry_commission

        outcome = None
        profit_loss = 0

        for i in range(breakout_idx + 1, len(df)):
            high_price = df.at[i, 'High']
            low_price = df.at[i, 'Low']

            if high_price >= tp:
                outcome = 'Successful'
                profit_loss = (tp - test_price) / test_price * balance * leverage
                break
            elif low_price <= sl:
                outcome = 'Unsuccessful'
                profit_loss = (test_price - sl) / test_price * balance * leverage * -1
                break

        # Расчет комиссии при выходе
        exit_commission = (balance + profit_loss) * market_commission
        balance += profit_loss - exit_commission

        results.append({
            'setup': pair,
            'breakout_idx': breakout_idx,
            'outcome': outcome,
            'profit_loss': profit_loss,
            'balance_after_trade': balance
        })

    return results