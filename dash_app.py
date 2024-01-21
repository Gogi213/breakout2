from dash import html, dcc, Input, Output
import dash
from binance_api import get_top_futures_pairs, get_historical_futures_data
import plot
from analysis import find_pivot_high, find_pivot_low, find_pairs, find_low_pairs, validate_setup, validate_low_setup, find_breakout_candles

app = dash.Dash(__name__)

volume_threshold = 150000000
symbols = get_top_futures_pairs(volume_threshold=volume_threshold)

app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Чарт', children=[
            plot.create_layout_with_graph_and_list(symbols, symbols[0]),
            html.Div(id='breakout-statistics-table')
        ]),
        dcc.Tab(label='Сводка таблиц', children=[
            html.Div(id='content-tab-2')
        ])
    ])
])

@app.callback(
    [Output('currency-pair-graph', 'figure'),
     Output('breakout-statistics-table', 'children')],
    [Input(symbol, 'n_clicks') for symbol in symbols]
)
def update_graph(*args):
    ctx = dash.callback_context

    if not ctx.triggered:
        symbol = symbols[0]
    else:
        symbol = ctx.triggered[0]['prop_id'].split('.')[0]

    df = get_historical_futures_data(symbol)

    pivot_highs = find_pivot_high(df, left_bars=15, right_bars=15)
    valid_high_pairs = validate_setup(df, find_pairs(pivot_highs, df))  # Исправлено: добавлен аргумент df
    pivot_lows = find_pivot_low(df, left_bars=15, right_bars=15)
    valid_low_pairs = validate_low_setup(df, find_low_pairs(pivot_lows, df))  # Исправлено: добавлен аргумент df

    # Создание графика
    graph = plot.plot_support_resistance_with_annotations(df, valid_high_pairs, valid_low_pairs, symbol)

    # Создание таблицы статистики
    breakout_candles = find_breakout_candles(df, valid_high_pairs + valid_low_pairs)
    statistics_table_figure = plot.create_breakout_statistics_table(df, breakout_candles, symbol)  # Добавлен symbol

    # Оборачиваем Figure в компонент dcc.Graph для совместимости с Dash
    statistics_table = dcc.Graph(figure=statistics_table_figure, className="statistics-table")

    return graph, statistics_table