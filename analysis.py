# analysis.py
import pandas as pd

# Функции для расчета точек разворота
def find_pivot_high(df, left_bars, right_bars):
    highs = []
    for i in range(left_bars, len(df) - right_bars):
        if df['High'][i] == max(df['High'][i-left_bars:i+right_bars+1]):
            highs.append({'index': df.index[i], 'price': df['High'][i], 'type': 'high'})
        else:
            highs.append({'index': df.index[i], 'price': None, 'type': 'high'})
    return highs

def find_pivot_low(df, left_bars, right_bars):
    lows = []
    for i in range(left_bars, len(df) - right_bars):
        if df['Low'][i] == min(df['Low'][i-left_bars:i+right_bars+1]):
            lows.append({'index': df.index[i], 'price': df['Low'][i], 'type': 'low'})
        else:
            lows.append({'index': df.index[i], 'price': None, 'type': 'low'})
    return lows

# Функция для поиска пар точек
# analysis.py

def find_pairs(pivot_points, df):
    pairs = []
    used_tests = set()
    setup_counter = 1

    for i, point in enumerate(pivot_points):
        if point['price'] is not None:
            current_nATR = df.at[point['index'], 'nATR']
            if pd.notna(current_nATR):
                threshold = current_nATR / 2
                best_test = None
                for j in range(i + 1, len(pivot_points)):
                    next_point = pivot_points[j]
                    if next_point['price'] is not None and next_point['index'] not in used_tests:
                        price_diff = abs(next_point['price'] - point['price']) / point['price']
                        if pd.notna(price_diff) and price_diff <= threshold:
                            if best_test is None or (next_point['price'] > best_test['price'] and next_point['price'] <= point['price']):
                                best_test = next_point

                if best_test:
                    pair = {
                        'start': {'index': point['index'], 'price': point['price'], 'type': point['type']},
                        'end': {'index': best_test['index'], 'price': best_test['price'], 'type': 'test'},
                        'setup_number': setup_counter
                    }
                    pairs.append(pair)
                    setup_counter += 1
                    for k in range(best_test['index'], min(best_test['index'] + int(threshold), len(pivot_points))):
                        used_tests.add(pivot_points[k]['index'])

    # Удаление смежных сетапов, которые делят более одной свечи
    for i in range(len(pairs) - 1, 0, -1):
        current_pair = pairs[i]
        previous_pair = pairs[i - 1]

        if current_pair['start']['index'] <= previous_pair['end']['index']:
            # Удаляем текущий сетап, так как он смежен с предыдущим более чем на одну свечу
            del pairs[i]

    return pairs


def find_low_pairs(pivot_lows, df):
    pairs = []
    used_tests = set()
    setup_counter = 1

    for i, low_point in enumerate(pivot_lows):
        if low_point['price'] is not None:
            current_nATR = df.at[low_point['index'], 'nATR']
            if pd.notna(current_nATR):
                threshold = current_nATR / 2
                best_test = None
                for j in range(i + 1, len(pivot_lows)):
                    next_low = pivot_lows[j]
                    if next_low['price'] is not None and next_low['index'] not in used_tests:
                        price_diff = abs(next_low['price'] - low_point['price']) / low_point['price']
                        if pd.notna(price_diff) and price_diff <= threshold:
                            if best_test is None or (next_low['price'] < best_test['price'] and next_low['price'] >= low_point['price']):
                                best_test = next_low

                if best_test:
                    pair = {
                        'start': {'index': low_point['index'], 'price': low_point['price'], 'type': low_point['type']},
                        'end': {'index': best_test['index'], 'price': best_test['price'], 'type': 'test'},
                        'setup_number': setup_counter
                    }
                    pairs.append(pair)
                    setup_counter += 1
                    for k in range(best_test['index'], min(best_test['index'] + int(threshold), len(pivot_lows))):
                        used_tests.add(pivot_lows[k]['index'])

    # Удаление смежных сетапов, которые делят более одной свечи
    for i in range(len(pairs) - 1, 0, -1):
        current_pair = pairs[i]
        previous_pair = pairs[i - 1]

        if current_pair['start']['index'] <= previous_pair['end']['index']:
            # Удаляем текущий сетап, так как он смежен с предыдущим более чем на одну свечу
            del pairs[i]

    return pairs




# Функция для проверки валидности сетапа
def validate_setup(df, pairs):
    valid_pairs = []
    for pair in pairs:
        start_idx = df.index.get_loc(pair['start']['index'])
        end_idx = df.index.get_loc(pair['end']['index'])

        # Проверяем, что вершина и тест не на одной свече и расстояние между ними >= 15
        if start_idx != end_idx and end_idx - start_idx >= 15:
            peak_price = pair['start']['price']
            test_price = pair['end']['price']

            # Дополнительные проверки
            if test_price <= peak_price and all(df['High'][i] <= peak_price for i in range(start_idx + 1, end_idx)):
                valid_pairs.append(pair)

    return valid_pairs


def validate_low_setup(df, pairs):
    valid_pairs = []
    for pair in pairs:
        start_idx = df.index.get_loc(pair['start']['index'])
        end_idx = df.index.get_loc(pair['end']['index'])

        # Проверяем, что дно и тест не на одной свече и расстояние между ними >= 15
        if start_idx != end_idx and end_idx - start_idx >= 15:
            bottom_price = pair['start']['price']
            test_price = pair['end']['price']

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