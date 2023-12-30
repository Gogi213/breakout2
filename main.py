# main.py

from binance_api import preload_data  # Импорт функции для предварительной загрузки данных
from dash_app import app  # Импорт экземпляра приложения Dash из dash_app.py

if __name__ == '__main__':
    preload_data()  # Предварительная загрузка данных для всех валютных пар
    app.run_server(debug=True)  # Запуск сервера Dash