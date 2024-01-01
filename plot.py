import plotly.graph_objects as go
from dash import html, dcc
from analysis import find_breakout_candles, emulate_position_tracking
from plotly.subplots import make_subplots

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
    # Создание сетки графиков с 2 рядами
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, subplot_titles=(symbol, 'nATR'),
                        row_heights=[0.7, 0.3])

    # Добавление свечного графика
    candlestick = go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'])
    fig.add_trace(candlestick, row=1, col=1)

    # Добавление графика nATR
    fig.add_trace(go.Bar(x=df.index, y=df['nATR'], marker_color='blue'), row=2, col=1)

    # Словарь для хранения номеров сетапов по каждой свече
    setups_per_candle = {}

    # Нумерация вершин и тестов
    setup_number = 1
    for pairs, is_high in [(valid_high_pairs, True), (valid_low_pairs, False)]:
        for pair in pairs:
            for idx, _ in pair:
                if idx not in setups_per_candle:
                    setups_per_candle[idx] = {'numbers': [], 'is_high': is_high}
                setups_per_candle[idx]['numbers'].append(str(setup_number))
            setup_number += 1

    # Находим и аннотируем свечи пробоя для верхних и нижних сетапов
    for pairs, is_high in [(valid_high_pairs, True), (valid_low_pairs, False)]:
        breakout_candles = find_breakout_candles(df, pairs, is_high)
        for pair, breakout_idx in breakout_candles:
            peak_idx = pair[0][0]
            if peak_idx in setups_per_candle:
                setup_numbers = setups_per_candle[peak_idx]['numbers']
                if breakout_idx not in setups_per_candle:
                    setups_per_candle[breakout_idx] = {'numbers': setup_numbers, 'is_high': is_high}
                else:
                    setups_per_candle[breakout_idx]['numbers'].extend(setup_numbers)

    # Создание аннотаций
    for idx, setup_info in setups_per_candle.items():
        price = df.at[idx, 'High'] if setup_info['is_high'] else df.at[idx, 'Low']
        if price is not None:
            fig.add_annotation(x=idx, y=price,
                               text='/'.join(setup_info['numbers']),
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