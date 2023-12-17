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

def plot_support_resistance_with_annotations(df, valid_pairs):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                                         open=df['Open'],
                                         high=df['High'],
                                         low=df['Low'],
                                         close=df['Close'])])

    for pair in valid_pairs:
        for idx, price in pair:
            end_idx = min(len(df.index) - 1, df.index.get_loc(idx) + 15)
            fig.add_shape(type="line",
                          x0=idx, y0=price, x1=df.index[end_idx], y1=price,
                          line=dict(color="Black", width=1))

    add_percentage_annotations(fig, df, valid_pairs)

    fig.update_layout(
        autosize=True,
        height=700,  # Вы можете изменить это значение, чтобы подогнать под размер экрана
        margin=dict(l=50, r=50, b=100, t=100, pad=4)
    )

    return fig

def create_layout_with_graph_and_list(symbols, selected_symbol):
    graph = dcc.Graph(id='currency-pair-graph')
    symbol_list = html.Ul([html.Li(symbol, id=symbol, style={'cursor': 'pointer'}) for symbol in symbols])

    layout = html.Div([
        html.Div(graph, style={'width': '90%', 'display': 'inline-block'}),
        html.Div(symbol_list, style={'width': '10%', 'display': 'inline-block', 'vertical-align': 'top'})
    ], style={'display': 'flex'})

    return layout
