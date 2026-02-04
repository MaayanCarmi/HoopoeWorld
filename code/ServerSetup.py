__author__ = 'Maayan'
import os
import subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "\\Certificate")
CA = {"key": r"rootCA.key", "cert": r"rootCA.crt"}

def main():
    print(f"current working dir: {os.getcwd()}")
    if not os.path.exists(CA["key"]) or not os.path.exists(CA["cert"]):
        subprocess.run(args=f"openssl genrsa -out {CA["key"]} 4096".split(" "), check=True)
        subprocess.run(args=f"openssl req -x509 -new -nodes -key {CA["key"]} -sha256 -days 3650 -out {CA["cert"]} -subj \"/C=IL/O=HSL/CN=HoopoeWorld\"".split(" "), check=True)

    subprocess.run(args="openssl genrsa -out server.key 4096".split(" "), check=True)
    subprocess.run(args="openssl req -new -key server.key -out server.csr -config server.cnf".split(" "), check=True)
    subprocess.run(args=f"openssl x509 -req -in server.csr -CA {CA["cert"]} -CAkey {CA["key"]} -CAcreateserial -out server.crt -days 3650 -sha256 -extfile server.cnf -extensions v3_ca".split(" "), check=True)

    try:
        print("where pip? " + subprocess.run(args="where pip".split(" "), capture_output = True, text = True, check=True).stdout)
    except subprocess.CalledProcessError:
        print("need to install pip")
        return
    subprocess.run(args="pip install requests".split(" "), check=True)
    subprocess.run(args="pip install pandas".split(" "), check=True)
    subprocess.run(args="pip install openpyxl".split(" "), check=True)

if __name__ == "__main__":
    main()
