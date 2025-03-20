import socket
from threading import Thread
# In-memory data structures
peers = {}  # {peer_id: {"ip": str, "port": int, "files": [file_hashes]}}
files = {}  # {file_hash: {"piece_count": int, "nodes": [peer_ids]}}
#tracker_id = str(uuid.uuid4())  # Unique tracker ID

def new_connection(addr, conn):
    print(addr)
    while True:
        try:
            data = conn.recv(1024)
            print(data)
            break
            # TODO: process at tracker side
        except Exception as e:
            print(e)
            print('Error occurred!')
            break

def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def server_program(host, port):
    serversocket = socket.socket()
    serversocket.bind((host, port))

    serversocket.listen(10)

    while True:
        conn, addr = serversocket.accept()
        nconn = Thread(target=new_connection, args=(addr, conn))
        nconn.start()

if __name__ == "__main__":
    # hostname = socket.gethostname()
    hostip = get_host_default_interface_ip()
    port = 22236
    print("Listening on {}:{}".format(hostip, port))
    server_program(hostip, port)