import plotly.graph_objects as go
from dash import html, dcc
from analysis import find_breakout_candles, emulate_position_tracking

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

def plot_support_resistance_with_annotations(df, valid_high_pairs, valid_low_pairs, symbol):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                         open=df['Open'],
                                         high=df['High'],
                                         low=df['Low'],
                                         close=df['Close'])])

    # Словарь для хранения номеров сетапов по каждой свече
    setups_per_candle = {}

    # Нумерация вершин и тестов
    setup_number = 1
    for pairs, color in [(valid_high_pairs, "Black"), (valid_low_pairs, "Blue")]:
        for pair in pairs:
            main_peak = pair[0]
            tests = pair[1]
            for test in tests:
                if isinstance(test, tuple) and len(test) == 2:
                    idx, price = test
                else:
                    print(f"Некорректный формат данных для теста: {test}")
                    continue

                if main_peak[0] not in setups_per_candle:
                    setups_per_candle[main_peak[0]] = {'numbers': [], 'is_high': color == "Black"}
                if idx not in setups_per_candle:
                    setups_per_candle[idx] = {'numbers': [], 'is_high': color == "Black"}
                setups_per_candle[main_peak[0]]['numbers'].append(str(setup_number))
                setups_per_candle[idx]['numbers'].append(str(setup_number))

                # Добавление линий от вершины к тестам
                fig.add_shape(type="line",
                              x0=main_peak[0], y0=main_peak[1], x1=idx, y1=price,
                              line=dict(color=color, width=1))
            setup_number += 1

    # Создание аннотаций
    for idx, setup_info in setups_per_candle.items():
        price = df.at[idx, 'High'] if setup_info['is_high'] else df.at[idx, 'Low']
        if price is not None:
            fig.add_annotation(x=idx, y=price,
                               text='/'.join(setup_info['numbers']),
                               showarrow=False,
                               yshift=10 if setup_info['is_high'] else -10)

    fig.update_layout(
        title=symbol,
        autosize=True,
        margin=dict(l=50, r=50, b=100, t=100, pad=4)
    )

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
    total_breakouts = len(results)
    successful_breakouts = sum(1 for result in results if result['outcome'] == 'Successful')
    unsuccessful_breakouts = total_breakouts - successful_breakouts
    win_rate = successful_breakouts / total_breakouts if total_breakouts > 0 else 0
    sum_nATR_successful = sum(result['profit_loss'] for result in results if result['outcome'] == 'Successful')
    sum_nATR_unsuccessful = sum(result['profit_loss'] for result in results if result['outcome'] == 'Unsuccessful')
    total_sum = sum_nATR_successful + sum_nATR_unsuccessful

    # Создание таблицы
    fig = go.Figure(data=[go.Table(
        header=dict(values=['Валютная пара', 'Количество пробоев', 'Успешные', 'Неуспешные', 'Винрейт', 'Сумма nATR успешных', 'Сумма nATR/2 неуспешных', 'Сумма двух предыдущих пунктов']),
        cells=dict(values=[[symbol], [total_breakouts], [successful_breakouts], [unsuccessful_breakouts], [f"{win_rate:.2%}"], [sum_nATR_successful], [sum_nATR_unsuccessful], [total_sum]])
    )])

    return fig