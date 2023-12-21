import plotly.graph_objects as go
from dash import html, dcc

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
    for pairs in [valid_high_pairs, valid_low_pairs]:
        for pair in pairs:
            for idx, _ in pair:
                if idx not in setups_per_candle:
                    setups_per_candle[idx] = []
                setups_per_candle[idx].append(str(setup_number))
            setup_number += 1

    # Создание аннотаций
    for idx, setup_numbers in setups_per_candle.items():
        price = df.at[idx, 'High'] if idx in df.index else None
        if price is not None:
            fig.add_annotation(x=idx, y=price,
                               text='/'.join(setup_numbers),
                               showarrow=False,
                               yshift=10)

    # Добавление линий и аннотаций для верхних и нижних пар
    for pairs, color in [(valid_high_pairs, "Black"), (valid_low_pairs, "Blue")]:
        for pair in pairs:
            for idx, price in pair:
                end_idx = min(len(df.index) - 1, df.index.get_loc(idx) + 15)
                fig.add_shape(type="line",
                              x0=idx, y0=price, x1=df.index[end_idx], y1=price,
                              line=dict(color=color, width=1))

    add_percentage_annotations(fig, df, valid_high_pairs + valid_low_pairs)

    fig.update_layout(
        title=symbol,  # Добавляем название тикера как заголовок графика
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