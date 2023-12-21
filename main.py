# main.py

from dash_app import app  # Импорт экземпляра приложения Dash из dash_app.py

if __name__ == '__main__':
    app.run_server(debug=True)  # Запуск сервера Dash