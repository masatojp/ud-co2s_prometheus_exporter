#!/usr/bin/env python3

from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from random import randrange
import time
from urllib.parse import parse_qs, urlparse
import threading

from prometheus_client import start_http_server
from prometheus_client import Counter, Summary, Gauge

import json, re, serial, io

def data():

    regex = re.compile(r'CO2=(?P<co2>\d+),HUM=(?P<hum>\d+\.\d+),TMP=(?P<tmp>-?\d+\.\d+)')
    with serial.Serial("/dev/ttyACM0", 115200, timeout=6) as conn:
        conn.write("STA\r\n".encode())
        print(conn.readline().decode().strip())
        time.sleep(5)

        while True:
            line = conn.readline().decode().strip()
            m = regex.match(line)
            if not m is None:
                udco2s_raw_data = {
                    "time": int(datetime.now().timestamp()),
                    "stat": {
                        "co2ppm": int(m.group("co2")),
                        "humidity": float(m.group("hum")),
                        "temperature": float(m.group("tmp")),
                    }
                } 
                udco2s_data = json.dumps(udco2s_raw_data)

            #json読み込み
            json_udco2s      = json.loads(udco2s_data)
            
            #print(json_udco2s)

            temperature_rack_top    = json_udco2s['stat']['temperature']
            humidity_rack_top    = json_udco2s['stat']['humidity']
            co2_rack_top   = json_udco2s['stat']['co2ppm']


            #print(temperature_rack_top)
            #print(humidity_rack_top)
            #print(co2_rack_top)

            #prometheus用関数に設定
            humidity_gauge_rack_top.set(humidity_rack_top)
            temperature_gauge_rack_top.set(temperature_rack_top)
            co2_gauge_rack_top.set(co2_rack_top)
            
humidity_gauge_rack_top = Gauge('my_home_rack_top_humidity_udco2s', 'My Home Rack top humidity by UD-CO2S')
temperature_gauge_rack_top = Gauge('my_home_rack_top_temperature_udco2s', 'My Home Rack top temperature UD-CO2S')
co2_gauge_rack_top = Gauge('my_home_rack_top_co2_udco2s', 'My Home Rack top CO2 by UD-CO2S')


class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path.endswith('/error'):
            raise Exception('Error')

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(f'Hello World!! from {self.path} as GET'.encode('utf-8'))

    def do_POST(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path.endswith('/error'):
            raise Exception('Error')

        content_length = int(self.headers['content-length'])
        body = self.rfile.read(content_length).decode('utf-8')

        print(f'body = {body}')

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(f'Hello World!! from {self.path} as POST'.encode('utf-8'))

if __name__ == '__main__':
    thread_1 = threading.Thread(target=data)
    thread_1.start()
    start_http_server(8000)

    with ThreadingHTTPServer(('0.0.0.0', 8080), MyHTTPRequestHandler) as server:
        print(f'[{datetime.now()}] Server startup.')
        server.serve_forever()
    
