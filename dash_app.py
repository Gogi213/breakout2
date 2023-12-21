import dash
from dash import html, dcc, Input, Output
from binance_api import get_top_futures_pairs, get_historical_futures_data
import plot
from analysis import find_pivot_high, find_pivot_low, find_pairs, find_low_pairs, validate_setup, validate_low_setup

# Создаем Dash-приложение
app = dash.Dash(__name__)

# Получаем список валютных пар
symbols = get_top_futures_pairs(limit=20)

# Определяем макет приложения
app.layout = plot.create_layout_with_graph_and_list(symbols, symbols[0])

# Колбэк для обновления графика при выборе валютной пары
@app.callback(
    Output('currency-pair-graph', 'figure'),
    [Input(symbol, 'n_clicks') for symbol in symbols]
)
def update_graph(*args):
    ctx = dash.callback_context

    if not ctx.triggered:
        symbol = symbols[0]
    else:
        symbol = ctx.triggered[0]['prop_id'].split('.')[0]

    df = get_historical_futures_data(symbol)

    pivot_highs = find_pivot_high(df, left_bars=10, right_bars=10)
    valid_high_pairs = validate_setup(df, find_pairs(pivot_highs, df))
    pivot_lows = find_pivot_low(df, left_bars=10, right_bars=10)
    valid_low_pairs = validate_low_setup(df, find_low_pairs(pivot_lows, df))

    # Обновление графика с учетом обоих наборов данных
    return plot.plot_support_resistance_with_annotations(df, valid_high_pairs, valid_low_pairs, symbol)