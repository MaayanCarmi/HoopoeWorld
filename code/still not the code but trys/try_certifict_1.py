__author__ = 'Maayan'

import http.server
import ssl

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # If the user asks for the root "/" or "Fake.html", send the HTML file
        if self.path == "/" or self.path == "/Fake.html" or self.path == "":
            self.path = "../webpage/webPageFake.html"

        # SimpleHTTPRequestHandler will now look for the file in self.path
        # and automatically serve hello.css or clock.js if the HTML requests them.
        return super().do_GET()


# Define the address and port
server_address = ('0.0.0.0', 4443)

# Create the HTTP server using our custom MyHandler
httpd = http.server.HTTPServer(server_address, MyHandler)

# Create an SSL context
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile=r"..\webpage\cert.pem", keyfile=r"..\webpage\key.pem")

# Wrap the server socket with SSL
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

print(f"Serving HTTPS on {server_address[0]} port {server_address[1]}...")
httpd.serve_forever()
def main():
    pass


if __name__ == "__main__":
    main()
