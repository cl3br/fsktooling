from http.server import BaseHTTPRequestHandler, HTTPServer
from http.client import HTTPConnection, NotConnected
import random
import traceback
from typing import Optional


class OdfListener(BaseHTTPRequestHandler):
    def set_header(self):
        self.send_response_only(200)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-HOVTP-Environment", self.headers["X-HOVTP-Environment"])
        self.send_header("X-HOVTP-Last-Serial-Number", self.headers["X-HOVTP-Serial-Number"])
        self.end_headers()

    def do_OPTIONS(self):
        print(self.request)
        print(self.headers)
        self.set_header()

    def do_POST(self):
        self.set_header()
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        if content_length > 0:
            self.process_odf(post_data.decode("utf-8"))

    def process_odf(self, odf : str):
        pass


def run_server(request_handler_class, host_name, server_port):
    web_server = HTTPServer((host_name, server_port), request_handler_class)
    print("Server started http://%s:%s" % (host_name, server_port))

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    print("Server stopped.")


class OdfSender:
    def __init__(self, host_name: str, port="8080"):
        self.connection = HTTPConnection(host_name, port, timeout=1)

    def send_odf(self, odf: str, serial_number: Optional[int] = None):        
        odf_bytes = odf.encode("utf-8")
        if not serial_number:
            serial_number = random.randrange(999999999)
        headers = {"X-HOVTP-Session-Id": "a4e244de-97ad-48e9-9957-e4b5ad94b624",
                   "X-HOVTP-Environment": "Production",
                   "X-HOVTP-Venue": "FSK",
                   "X-HOVTP-Discipline": "FSK",
                   "X-HOVTP-Origin": "OVR-FSK",
                   "X-HOVTP-Data-Type": "ODF",
                   "X-HOVTP-Serial-Number": str(serial_number),
                   "Content-Type": "text/xml",
                   "Host": self.connection.host,
                   "Cache-Control": "no-store, no-cache",
                   "Pragma": "no-cache",
                   "Content-Length": len(odf_bytes),
                   "Connection": "Keep-Alive"}
        try:
            self.connection.request("POST", "", odf_bytes, headers)
            r = self.connection.getresponse()
            print(r.code)
            if r.code != 200:
                print("Error")
            if r.headers["X-HOVTP-Last-Serial-Number"] != str(serial_number):
                print("Warning. Serial number does not match.")
            print(r.read().decode())
        except:
            print(f"No connection for {self.connection.host}:{self.connection.port}")
            # traceback.print_exc()
            pass


class OdfMultiplexer(OdfListener):
    def __init__(self, request, client_address, server):
        self.senders = [OdfSender("localhost", "11112"), OdfSender("localhost", "11113")]
        super().__init__(request, client_address, server)

    def process_odf(self, odf: str):
        for sender in self.senders:
            sender.send_odf(odf)


if __name__ == "__main__":
    run_server(OdfMultiplexer, "localhost", 11111)
