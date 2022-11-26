from http.server import BaseHTTPRequestHandler, HTTPServer


class OdfListener(BaseHTTPRequestHandler):
    def set_header(self):
        self.send_response_only(200)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-HOVTP-Environment", self.headers["X-HOVTP-Environment"])
        self.send_header("X-HOVTP-Last-Serial-Number", self.headers["X-HOVTP-Last-Serial-Number"])
        self.end_headers()

    def do_OPTIONS(self):
        self.set_header()

    def do_POST(self):
        self.set_header()
        print(self.headers)
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        if content_length > 0:
            print(post_data)
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
