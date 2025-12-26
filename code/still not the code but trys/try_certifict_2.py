__author__ = 'Maayan'

import http.server
import ssl
import os


class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"Received request for: {self.path}")  # DEBUG PRINT
        # If the user asks for the root, give them the HTML file
        if self.path == "/" or self.path == "":
            self.path = "/webPageFake.html"

        # SimpleHTTPRequestHandler handles the rest (CSS and JS)
        # as long as they are in this same folder.
        return super().do_GET()


# Server settings
server_address = ('0.0.0.0', 4443)
httpd = http.server.HTTPServer(server_address, MyHandler)

# SSL Setup
# Since everything is in one folder, we don't need ".." paths anymore
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

# Wrap the socket
httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

print(f"Server started at https://localhost:4443")
print("Files in directory:", os.listdir('.'))  # Helps you verify files are visible
httpd.serve_forever()

def main():
    pass


if __name__ == "__main__":
    main()
