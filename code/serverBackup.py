__author__ = 'Maayan'
import ssl, json, threading, socket, os
import DecodeDataInPacket as DDIP

threads = []
website_folder = "webpage"

def set_header_type(file_name):
    """
    get the Content-Type for files
    :param file_name: what is the full name (with the .)
    :return: file type for http
    """
    file_ending = file_name[file_name.rindex(".") + 1:]
    if file_ending == "html":
        return f"text/html; charset=utf-8"
    elif file_ending == "txt":
        return "text/plain"
    elif file_ending == "js":
        return "text/javascript; charset=utf-8"
    elif file_ending == "css":
        return "text/css"
    elif file_ending == "xlsx":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif file_ending in ["ico", "jpeg", "jpg", "png", "gif"]:
        return f"image/{file_ending}"
    return "unknown"


def get_http_get_msg(sock) -> tuple:
    """
    get the request from the client (mostly the url)
    :param sock: the client socket.
    :return: (if it is a get request, path/url)
    """
    data = b""
    while b"\r\n\r\n" not in data:
        data_to_add = sock.recv(1024)
        if data_to_add != b"":
            data += data_to_add
    data = data.decode()
    if "GET" in data:
        return True, data.split(" ")[1]
    elif "POST" in data:
        return False, ""
    return False, ""

class Handler(threading.Thread):
    def __init__(self, path, sock, is_get):
        """
        get the super from thread and also params about the request.
        :param path: what was the path (the url)
        :param sock: client soket already wrap with ssl.
        :param is_get: check if there is get (if not return bad format because I don't have post)
        """
        super().__init__()
        self.path = path
        self.__sock = sock
        self.__header = {
            "Content-Type": "text" #default
        }
        self.code = 200
        self.__is_get = is_get

    def set_headers(self, header, data):
        """
        add header with info to the dict. also no length (added on send)
        :param header: name of the header (ex. Content-Type)
        :param data: type, info. (ex. text/html)
        :return: none, change param from init
        """
        if header == "Content-Length": return
        self.__header[header] = data

    def headers_send(self) -> str:
        """
        make the headers that where added in the format of http
        :return: str, headerName: info\r\n ...
        """
        return "\r\n".join(f"{key}: {self.__header[key]}" for key in self.__header.keys())

    def create_scroll(self, top:bool) -> tuple:
        """
        create send for both top and bottom. create the params for the html.
        :param top: a True or False if it's a request for top or bottom.
        :return: the html to add, what the oldest got, what the newest got.
        """
        # if the code has an error the except id outside.
        params = self.path.split("?")[-1].split("&")  # get the params from the request.
        params = {param.split("=")[0]: param.split("=")[1].replace("%20", " ") for param in params}  # split according to the protocol
        # also get and in case of a space add it.
        sat_name, most_resent = params["satName"], params["mostResent"] if top else params["leastResent"]
        limit = 25 if not top else 0
        html, oldest, newest = DDIP.make_for_html(sat_name, most_resent, top, limit, int(params["width"]))  # according to the function in decode.
        # make headers.
        self.set_headers("Content-Type", "application/json")
        self.code = 200
        return html, oldest, newest

    def send(self, data=b""):
        """
        sending the response for the request from the client.
        header and code takes from init. Also deal with errors.
        :param data: the data that is going to be in the body
        :return: none
        """
        data_to_send = b""
        if self.code == 200:
            data_to_send += f"HTTP/1.1 200 OK\r\n{self.headers_send()}\r\nContent-Length: {len(data)}\r\n\r\n".encode() + data
        elif self.code == 404:
            data_to_send += b"HTTP/1.1 404 Not Found"
        elif self.code == 400:
            data_to_send += b"HTTP/1.1 400 Bad Request"
        print(f"sent >> {data_to_send[:150]}")
        self.__sock.send(data_to_send)

    def run(self):
        """
        override the run of thread, but have the full client logic
        :return: none
        """
        print(f"Received request for: {self.path}")
        if not self.__is_get:
            self.code = 400
            self.send()
        try:
            # check request according to protocol
            if self.path.startswith("/chooseSatellite/"):
                # think of the create_send just for choose sat (without the start time because we never got a thing)
                params = self.path.split("?")[-1].split("&")  # get the params from the request.
                params = {param.split("=")[0]: param.split("=")[1].replace("%20", " ") for param in params}
                sat_name = params["satName"]
                html, oldest, newest = DDIP.make_for_html(sat_name, 0, True, 25, int(params["width"]))

                self.code = 200
                self.__con_type = "application/json"
                # send to json of the data back.
                self.send(json.dumps({"mostResent":newest, "leastResent":oldest, "data":html}).encode("utf-8"))
                return
                # protocol chooseSatellite/satName
            elif self.path.startswith("/addTop/"):
                html, oldest, newest = self.create_scroll(True) #is top
                # send to json of the data back.
                self.send(json.dumps({"mostResent":newest, "data":html}).encode("utf-8"))
                return
                # protocol addTop/?satName={}&mostResent={}
            elif self.path.startswith("/addBottom/"):
                html, oldest, newest = self.create_scroll(False) #isn't top
                # send to json of the data back.
                self.send(json.dumps({"leastResent":oldest, "data":html}).encode("utf-8"))
                return
                # protocol addBottom/?satName={}&leastResent={}
            elif self.path.startswith("/downloadData/"):
                params = self.path.split("?")[-1].split("&")
                params = {param.split("=")[0]: param.split("=")[1].replace("%20", " ") for param in params} #get params
                excel, file_name = DDIP.make_excel(params) #make excel
                #make the needed headers that with them the client will know he needs to download it to the computer.
                self.code = 200
                self.set_headers('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                self.set_headers('Content-Disposition', f'attachment; filename="{file_name}.xlsx"')
                self.send(excel.getvalue()) #send Excel file.
                excel.close()
                return
                #protocol: downloadData/?type={typeOfDownload}&satName={}&limit={} or &start={}&end={} or &start={} or none.
            else:
                if self.path == "/" or self.path == "":
                    self.path = f"{website_folder}/hoopoeWorld.html" #have the current sats at selection and the main page.
                else: self.path = f"{website_folder}{self.path}"
                print(f"Changed request for: {self.path}")
                if os.path.exists(self.path):
                    self.set_headers("Content-Type", set_header_type(self.path))
                    with open(self.path, 'rb') as f:
                        self.send(f.read())
                else:
                    self.code = 404
                    self.send()
        except Exception as e: #in case of an error send error
            print(f"error {e}")
            self.code = 400
            self.send()
        finally:
            self.__sock.close()

def https_server():
    """
    https server thread. here I create the class and the start of the https
    :return: None
    """
    server_address = ('0.0.0.0', 443)
    # SSL Setup
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="Certificate/server.crt", keyfile="Certificate/server.key") #get the Certificate

    server_socket = socket.socket()
    server_socket.bind(server_address)  # Using 4433 for testing
    server_socket.listen(20)
    global threads
    try:
        while True:
            cli_sock, addr = server_socket.accept()
            connstream = context.wrap_socket(cli_sock, server_side=True)

            is_get, path = get_http_get_msg(connstream)
            t = Handler(path=path, sock=connstream, is_get=is_get)
            t.start()
            threads.append(t)

            # removes finished threads from the list
            for k in threads:
                if not k.is_alive(): k.join()
            threads = [t for t in threads if t.is_alive()]
    finally:
        server_socket.close()


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
