__author__ = 'Maayan'
import os
import subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "\\Certificate")
CA = {"key": r"rootCA.key", "cert": r"rootCA.crt"}

def main():
    if not os.path.exists(CA["key"]) or not os.path.exists(CA["cert"]):
        subprocess.run(args=f"openssl genrsa -out {CA["key"]} 4096".split(" "), check=True)
        subprocess.run(args=f"openssl req -x509 -new -nodes -key {CA["key"]} -sha256 -days 3650 -out {CA["cert"]} -subj \"/C=IL/O=HSL/CN=HoopoeWorld\"".split(" "), check=True)

    subprocess.run(args="openssl genrsa -out server.key 4096".split(" "), check=True)
    subprocess.run(args="openssl req -new -key server.key -out server.csr -config server.cnf".split(" "), check=True)
    subprocess.run(args=f"openssl x509 -req -in server.csr -CA {CA["cert"]} -CAkey {CA["key"]} -CAcreateserial -out server.crt -days 3650 -sha256 -extfile server.cnf -extensions v3_ca".split(" "), check=True)


if __name__ == "__main__":
    main()
