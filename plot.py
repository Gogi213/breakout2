import plotly.graph_objects as go
import logging
from dash import html, dcc
from analysis import find_breakout_candles, emulate_position_tracking
from plotly.subplots import make_subplots

logging.basicConfig(level=logging.INFO)

def add_percentage_annotations(fig, df, pairs):
    for pair in pairs:
        start_price = pair[0][1]
        end_price = pair[1][1]
        percentage_change = ((end_price - start_price) / start_price) * 100

        start_idx = df.index.get_loc(pair[0][0])
        end_idx = df.index.get_loc(pair[1][0])
        x_position = df.index[int((start_idx + end_idx) / 2)]

        fig.add_annotation(x=x_position, y=start_price,
                           text=f"{percentage_change:.2f}%",
                           showarrow=True,
                           arrowhead=1)

import plotly.graph_objects as go

def plot_support_resistance_with_annotations(df, valid_high_pairs, valid_low_pairs, symbol):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, subplot_titles=(symbol, 'nATR'),
                        row_heights=[0.7, 0.3])

    candlestick = go.Candlestick(x=df['Formatted Open Time'], open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'])
    fig.add_trace(candlestick, row=1, col=1)

    # Добавление графика nATR
    fig.add_trace(go.Bar(x=df['Formatted Open Time'], y=df['nATR'], marker_color='blue'), row=2, col=1)

    # Словарь для хранения номеров сетапов по каждой свече
    setups_per_candle = {}

    setup_number = 1
    for pairs, is_high in [(valid_high_pairs, True), (valid_low_pairs, False)]:
        for pair in pairs:
            # Определение типов свечей в паре
            if len(pair) == 2:  # Если в сетапе две свечи
                peak_idx, test_idx = pair[0][0], pair[1][0]
                peak_time = df.at[peak_idx, 'Formatted Open Time']
                test_time = df.at[test_idx, 'Formatted Open Time']
                setups_per_candle[peak_idx] = {'numbers': [str(setup_number)], 'is_high': is_high, 'type': 'peak',
                                               'time': peak_time}
                setups_per_candle[test_idx] = {'numbers': [str(setup_number)], 'is_high': is_high, 'type': 'test',
                                               'time': test_time}
            elif len(pair) > 2:  # Если в сетапе более двух свечей
                peak_idx = pair[0][0]
                breakout_idx = pair[-1][0]
                peak_time = df.at[peak_idx, 'Formatted Open Time']
                breakout_time = df.at[breakout_idx, 'Formatted Open Time']
                setups_per_candle[peak_idx] = {'numbers': [str(setup_number)], 'is_high': is_high, 'type': 'peak',
                                               'time': peak_time}
                setups_per_candle[breakout_idx] = {'numbers': [str(setup_number)], 'is_high': is_high,
                                                   'type': 'breakout', 'time': breakout_time}
                # Остальные свечи считаются тестами
                for idx, _ in pair[1:-1]:
                    test_time = df.at[idx, 'Formatted Open Time']
                    if idx not in setups_per_candle:
                        setups_per_candle[idx] = {'numbers': [str(setup_number)], 'is_high': is_high, 'type': 'test',
                                                  'time': test_time}
                    else:
                        setups_per_candle[idx]['numbers'].append(str(setup_number))
                        # Обновляем время, если оно не было установлено ранее
                        if 'time' not in setups_per_candle[idx]:
                            setups_per_candle[idx]['time'] = test_time

            setup_number += 1

    # Находим и аннотируем свечи пробоя для верхних и нижних сетапов
    for pairs, is_high in [(valid_high_pairs, True), (valid_low_pairs, False)]:
        breakout_candles = find_breakout_candles(df, pairs, is_high)
        for pair, breakout_idx in breakout_candles:
            peak_idx = pair[0][0]
            if peak_idx in setups_per_candle:
                setup_numbers = setups_per_candle[peak_idx]['numbers']
                breakout_time = df.at[breakout_idx, 'Formatted Open Time']
                if breakout_idx not in setups_per_candle:
                    setups_per_candle[breakout_idx] = {'numbers': setup_numbers, 'is_high': is_high, 'type': 'breakout',
                                                       'time': breakout_time}
                else:
                    setups_per_candle[breakout_idx]['numbers'].extend(setup_numbers)
                    setups_per_candle[breakout_idx]['type'] = 'breakout'  # Явно указываем тип пробойной свечи
                    # Обновляем время, если оно не было установлено ранее
                    if 'time' not in setups_per_candle[breakout_idx]:
                        setups_per_candle[breakout_idx]['time'] = breakout_time

    # Создание аннотаций
    for idx, setup_info in setups_per_candle.items():
        price = df.at[idx, 'High'] if setup_info['is_high'] else df.at[idx, 'Low']
        if price is not None:
            fig.add_annotation(x=df.at[idx, 'Formatted Open Time'], y=price,
                               text=setup_info['numbers'][0],
                               showarrow=False,
                               yshift=10 if setup_info['is_high'] else -10,
                               row=1, col=1)

    # Обновление макета графика
    fig.update_layout(
        height=800, width=1200, title_text="График с nATR",
        showlegend=False,  # Отключение легенды
        margin=dict(l=50, r=50, b=100, t=100, pad=4)
    )
    fig.update_xaxes(title_text="Дата", row=2, col=1)
    fig.update_yaxes(title_text="Цена", row=1, col=1)
    fig.update_yaxes(title_text="nATR", row=2, col=1)

    # Отключение кнопок 'Trace' в верхнем правом углу
    fig.update_layout(updatemenus=[dict(type="buttons", showactive=False)])

    logging.info("Содержимое setups_per_candle: %s", setups_per_candle)

    return fig


def create_layout_with_graph_and_list(symbols, selected_symbol):
    graph = dcc.Graph(id='currency-pair-graph', style={'height': '100vh'})  # Задаем высоту графика
    symbol_list = html.Ul(
        [html.Li(symbol, id=symbol, className='symbol-item', n_clicks=0) for symbol in symbols],
        style={'list-style-type': 'none', 'padding': '0'}  # Убираем маркеры списка и отступы
    )

    layout = html.Div([
        html.Div(graph, style={'width': '90%', 'display': 'inline-block'}),
        html.Div(symbol_list, style={'width': '10%', 'display': 'inline-block', 'vertical-align': 'top', 'margin-top': '100px'})
    ], style={'display': 'flex', 'height': '100vh'})

    return layout

def create_breakout_statistics_table(df, breakout_candles, symbol):
    # Получение результатов эмуляции
    results = emulate_position_tracking(df, breakout_candles)

    # Сбор статистики
    total_trades = len(results)
    successful_trades = sum(1 for result in results if result['outcome'] == 'Successful')
    unsuccessful_trades = total_trades - successful_trades
    win_rate = successful_trades / total_trades if total_trades > 0 else 0
    total_profit = sum(result['profit_loss'] for result in results)
    profit_factor = sum(result['profit_loss'] for result in results if result['profit_loss'] > 0) / abs(sum(result['profit_loss'] for result in results if result['profit_loss'] < 0)) if unsuccessful_trades > 0 else 'inf'

    # Создание таблицы
    fig = go.Figure(data=[go.Table(
        header=dict(values=['Валютная пара', 'Всего сделок', 'Успешных', 'Неуспешных', 'Winrate', 'Доход', 'Профит фактор']),
        cells=dict(values=[[symbol], [total_trades], [successful_trades], [unsuccessful_trades], [f"{win_rate:.2%}"], [total_profit], [profit_factor]])
    )])

    return fig
