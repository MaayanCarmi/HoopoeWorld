__author__ = 'Maayan'
import http.server, socketserver, ssl, json, threading
import DecodeDataInPacket as DDIP

website_folder = "/webpage"

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """make the Handle requests in a separate thread."""
    daemon_threads = True

class Handler(http.server.SimpleHTTPRequestHandler):
    def create_send(self, top):
        """
        create send for both top and bottom. create the params for the html.
        :param top: a True or False if it's a request for top or bottom.
        :return: the html to add, what the oldest got, what the newest got.
        """
        #if the code has an error the except id outside.
        params = self.path.split("?")[-1].split("&") #get the params from the request.
        params = {param.split("=")[0]: param.split("=")[1].replace("%20", " ") for param in params} #split according to the protocol
        # also get and in case of a space add it.
        sat_name, most_resent = params["satName"], params["mostResent"] if top else params["leastResent"]
        limit = 25 if not top else 0
        html, oldest, newest = DDIP.make_for_html(sat_name, most_resent, top, limit) #according to the function in decode.
        #make headers.
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        return html, oldest, newest

    def do_GET(self):
        """
        do all the GET requests, it overwrites the function but at the end also used it.
        :return: nothing
        """
        print(f"Received request for: {self.path}")
        try:
            # check request according to protocol
            if self.path.startswith("/chooseSatellite/"):
                # think of the create_send just for choose sat (without the start time because we never got a thing)
                sat_name = self.path.split("/")[-1].replace("%20", " ")
                html, oldest, newest = DDIP.make_for_html(sat_name, 0, True, 25)
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                # send to json of the data back.
                self.wfile.write(json.dumps({"mostResent":newest, "leastResent":oldest, "data":html}).encode("utf-8"))
                return
                # protocol chooseSatellite/satName
            elif self.path.startswith("/addTop/"):
                html, oldest, newest = self.create_send(True) #is top
                # send to json of the data back.
                self.wfile.write(json.dumps({"mostResent":newest, "data":html}).encode("utf-8"))
                return
                # protocol addTop/?satName={}&mostResent={}
            elif self.path.startswith("/addBottom/"):
                html, oldest, newest = self.create_send(False) #isn't top
                # send to json of the data back.
                self.wfile.write(json.dumps({"leastResent":oldest, "data":html}).encode("utf-8"))
                return
                # protocol addBottom/?satName={}&leastResent={}
            elif self.path.startswith("/downloadData/"):
                params = self.path.split("?")[-1].split("&")
                params = {param.split("=")[0]: param.split("=")[1].replace("%20", " ") for param in params} #get params
                excel, file_name = DDIP.make_excel(params) #make excel
                #make the needed headers that with them the client will know he needs to download it to the computer.
                self.send_response(200)
                self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                self.send_header('Content-Disposition', f'attachment; filename="{file_name}.xlsx"')
                self.end_headers()
                self.wfile.write(excel.getvalue()) #send Excel file.
                excel.close()
                print("hello")
                return
                #protocol: downloadData/?type={typeOfDownload}&satName={}&limit={} or &start={}&end={} or &start={} or none.
        except Exception as e: #in case of an error send error
            print(f"error {e}")
            self.send_response(404)
            self.end_headers()
            self.wfile.write("had an error".encode())

        # get normal static files. default if it's not other stuff.
        if self.path == "/" or self.path == "":
            self.path = f"{website_folder}/hoopoeWorld.html" #have the current sats at selection and the main page.
        else: self.path = f"{website_folder}{self.path}"
        print(f"Changed request for: {self.path}")
        return super().do_GET()


def https_server():
    """
    https server thread. here I create the class and the start of the https
    :return: None
    """
    server_address = ('0.0.0.0', 443)
    httpd = http.server.HTTPServer(server_address, Handler) #make it with the class above.

    # SSL Setup
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="Certificate/cert.pem", keyfile="Certificate/key.pem") #get the Certificate
    # Wrap the socket (to be with SSL)
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    httpd.serve_forever() #run the http until we can't

def main():
    try:
        DDIP.create_tables() #make sure all the tables are created
        #Create the selection from the json and template. Used while the server is active reset each run.
        with open(r"webpage\templateWebsite.html", 'r') as file:
            website = file.read()
        website = website.replace("<!--Server-->", DDIP.create_options())
        with open(r"webpage\hoopoeWorld.html", 'w') as file:
            file.write(website)

        try: #create class with the pass times or without.
            with open("../jsons/newestTime.json", "r") as file:
                packets_to_sql = DDIP.SatNogsToSQL(json.load(file))
        except OSError or Exception: packets_to_sql = DDIP.SatNogsToSQL()
        https_thread = threading.Thread(target=https_server)
        https_thread.start() #thread of https.
        packets_to_sql.infinite_loop() #call the loop.


    finally:
        packets_to_sql.run = False
        https_thread.join() #close it.
        DDIP.connection_sql.close()
        # It doesn't really matter if we have an error here. because the only way to have it's because of other error.


if __name__ == "__main__":
    main()
