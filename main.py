import json
import logging
import socket
import urllib.parse as url
import mimetypes
import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

HOME_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = 'localhost'
SOCKET_HOST = '127.0.0.1'
SOCKET_PORT = 5000


class MyFirstHTTPServer(BaseHTTPRequestHandler):

    def do_GET(self):
        route = url.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file_name = HOME_DIR.joinpath(route.path[1:])
                if file_name.exists():
                    self.send_static(file_name)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        length = self.headers.get('Content-length')
        data = self.rfile.read(int(length))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()
        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fl:
            self.wfile.write(fl.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mimetype, *_ = mimetypes.guess_type(filename)
        if mimetype:
            self.send_header('Content-Type', mimetype)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file_static:
            self.wfile.write(file_static.read())


def save_data_from_form(data):
    data_time = str(datetime.datetime.now())
    parse_data = data.decode()
    try:
        parse_to_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        check_json(data_time,parse_to_dict)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)


def check_json(data_time, parde_dict):
    try:
        with open('storage/data.json', 'r') as l_file:
            reader = json.load(l_file)
        reader[data_time] = parde_dict
        with open('storage/data.json', 'w', encoding='utf-8') as f_json:
            json.dump(reader, f_json, ensure_ascii=False, indent=4)
    except:
        start_json = {data_time: parde_dict}
        with open('storage/data.json', 'w', encoding='utf-8') as f_json:
            json.dump(start_json, f_json, ensure_ascii=False, indent=2)


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            save_data_from_form(msg)
    except KeyboardInterrupt:
        server_socket.close()
    finally:
        server_socket.close()


def run_http_server(host, port):
    address = (host, port)
    server_http = HTTPServer(address, MyFirstHTTPServer)

    try:
        server_http.serve_forever()
    except KeyboardInterrupt:
        server_http.server_close()
    finally:
        server_http.server_close()


if __name__ == '__main__':

    http_server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    http_server.start()

    socket_server = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    socket_server.start()
