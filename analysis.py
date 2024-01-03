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

def find_breakout_candles(df, pairs, setup_numbers, is_high=True, min_candles_after_test=5):
    breakout_candles = []

    for index, pair in enumerate(pairs):
        peak_idx, peak_price = pair[0]
        test_idx, test_price = pair[1]
        current_setup_number = setup_numbers[index]

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
                    # Определяем аннотацию для пробойной свечи
                    if i == peak_idx:
                        # Если пробойная свеча является вершиной следующего сетапа
                        next_setup_number = setup_numbers[index + 1] if index + 1 < len(setup_numbers) else current_setup_number
                        setup_label = f"{next_setup_number}/{current_setup_number}"
                    else:
                        setup_label = str(current_setup_number)
                    breakout_candles.append((pair, i, setup_label))
                    break
            else:
                # Аналогичная логика для нижних сетапов
                if candle['High'] >= test_price and candle['Low'] <= test_price:
                    if i == peak_idx:
                        next_setup_number = setup_numbers[index + 1] if index + 1 < len(setup_numbers) else current_setup_number
                        setup_label = f"{next_setup_number}/{current_setup_number}"
                    else:
                        setup_label = str(current_setup_number)
                    breakout_candles.append((pair, i, setup_label))
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

def process_setups(df, left_bars, right_bars):
    # Шаг 1: Нахождение вершин и донных точек
    pivot_highs = find_pivot_high(df, left_bars, right_bars)
    pivot_lows = find_pivot_low(df, left_bars, right_bars)

    # Шаг 2: Формирование пар вершина-тест
    high_pairs = find_pairs(pivot_highs, df)
    low_pairs = find_low_pairs(pivot_lows, df)

    # Шаг 3: Валидация сетапов
    valid_high_pairs = validate_setup(df, high_pairs)
    valid_low_pairs = validate_low_setup(df, low_pairs)

    # Шаг 4: Сохранение информации о сетапах
    setups = valid_high_pairs + valid_low_pairs  # Пример объединения верхних и нижних сетапов

    # Шаг 5: Отслеживание смежности сетапов
    setups_adjacency = {}  # Словарь для хранения смежности

    for i in range(len(setups) - 1):
        current_setup = setups[i]
        next_setup = setups[i + 1]
        # Проверяем, является ли последняя свеча текущего сетапа первой свечей следующего сетапа
        if current_setup[-1]['index'] == next_setup[0]['index']:
            setups_adjacency[current_setup[-1]['index']] = (i, i + 1)

    # Возвращаем сетапы и информацию о смежности
    return setups, setups_adjacency

