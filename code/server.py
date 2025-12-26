__author__ = 'Maayan'
import http.server, socketserver, ssl
import DecodeDataInPacket as DDIP

website_folder = "/webpage"

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """make the Handle requests in a separate thread."""
    daemon_threads = True

class Handler(http.server.SimpleHTTPRequestHandler):
    def create_send(self, top):
        params = self.path.split("/")[-1]
        params = params.split("?")
        sat_name = params[0].split("=")[1]
        most_resent = params[1].split("=")[1]
        html, oldest, newest = DDIP.make_for_html(sat_name, most_resent, top)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        return html, oldest, newest

    def do_GET(self):
        if self.path.startswith("/chooseSatellite/"):
            sat_name = self.path.split("/")[-1]
            html, oldest, newest = DDIP.make_for_html(sat_name, 0, True)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(f"mostResent={newest}|lestResent={oldest}|data={html}".encode("utf-8"))
            # protocol chooseSatellite/satName
        elif self.path.startswith("/addTop/"):
            html, oldest, newest = self.create_send(True)
            self.wfile.write(f"mostResent={newest}|data={html}".encode("utf-8"))
            # protocol addTop/satName={}?mostResent={}
        elif self.path.startswith("/addBottom/"):
            html, oldest, newest = self.create_send(False)
            self.wfile.write(f"lestResent={oldest}|data={html}".encode("utf-8"))
            # protocol addBottom/satName={}?lestResent={}
        #todo: need to create the js for this. and add a lot of comments.

        # get normal static files.
        if self.path == "/" or self.path == "":
            self.path = f"{website_folder}/currentWebsite.html"
            #at the start of the program I create this to be from template and add the needed names to selection. (happened before)
            #one will be saved as template "templateWebsite.html" and one as the "currentWebsite.html"
        else:
            self.path = f"{website_folder}{self.path}"
        print(f"Received request for: {self.path}")
        return super().do_GET()


def main():
    try:
        #Create the selection from the json and template. Used while the server is active reset each run.
        with open(r"webpage\templateWebsite.html", 'r') as file:
            website = file.read()
        website = website.replace("<!--Server-->", DDIP.create_options())
        with open(r"webpage\currentWebsite.html", 'w') as file:
            file.write(website)

        #call here to the infinite loop in thread

        server_address = ('0.0.0.0', 443)
        httpd = http.server.HTTPServer(server_address, Handler)

        # SSL Setup
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile="Certificate/cert.pem", keyfile="Certificate/key.pem")
        # Wrap the socket (to be with SSL)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)


        httpd.serve_forever()
    finally:
        pass


if __name__ == "__main__":
    main()
