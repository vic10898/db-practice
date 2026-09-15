import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from db_service import get_connection, init_database, get_partner_with_discount, get_all_partners_with_discounts

PORT = 8000


class PartnerAPIHandler(BaseHTTPRequestHandler):
    """
    HTTP-обработчик запросов для взаимодействия с клиентской стороной (JavaScript / UI).
    Предоставляет REST API в формате JSON.
    """

    def _set_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path.rstrip("/")

        # Маршрут получения списка всех партнеров со скидками
        if path == "/api/partners":
            partners = get_all_partners_with_discounts()
            self._set_headers(200)
            response_data = json.dumps(partners, ensure_ascii=False, indent=2)
            self.wfile.write(response_data.encode("utf-8"))
            return

        # Маршрут получения конкретного партнера по ID: /api/partners/<id>
        if path.startswith("/api/partners/"):
            parts = path.split("/")
            if len(parts) == 4 and parts[3].isdigit():
                partner_id = int(parts[3])
                partner = get_partner_with_discount(partner_id)
                if partner is not None:
                    self._set_headers(200)
                    response_data = json.dumps(partner, ensure_ascii=False, indent=2)
                    self.wfile.write(response_data.encode("utf-8"))
                    return
                else:
                    self._set_headers(404)
                    error_data = json.dumps({"error": "Партнер не найден"}, ensure_ascii=False)
                    self.wfile.write(error_data.encode("utf-8"))
                    return

        # Корневой маршрут со справкой
        if path == "" or path == "/api":
            self._set_headers(200)
            info = {
                "message": "API для работы с партнерами и расчета скидок",
                "endpoints": [
                    {"method": "GET", "url": "/api/partners", "description": "Список всех партнеров со скидками"},
                    {"method": "GET", "url": "/api/partners/<id>", "description": "Данные партнера по ID со скидкой"}
                ]
            }
            self.wfile.write(json.dumps(info, ensure_ascii=False, indent=2).encode("utf-8"))
            return

        # Маршрут не найден
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Страница не найдена"}, ensure_ascii=False).encode("utf-8"))

    def log_message(self, format, *args):
        # Отключаем вывод стандартных логов запросов в консоль
        return


def run_server(port=PORT):
    conn = get_connection()
    init_database(conn)
    conn.close()

    server_address = ("", port)
    httpd = HTTPServer(server_address, PartnerAPIHandler)
    print(f"Сервер API успешно запущен на http://localhost:{port}/api/partners")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
