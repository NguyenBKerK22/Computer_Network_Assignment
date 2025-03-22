import socket
import time
from idlelib import query
from threading import Thread
from urllib.parse import urlparse, parse_qs
import bencodepy
import requests
# In-memory data structures
peers = [] # {peer_id: {"ip": str, "port": int, "files": [file_hashes]}}
files = {}  # {file_hash: {"piece_count": int, "nodes": [peer_ids]}}
tracker_id = "hehehehehehehehehehe"  # Unique tracker ID

def new_connection(addr, conn):
    print(addr)
    while True:
        try:
            data = conn.recv(1024).decode()
            lines = data.split("\r\n")

            # Lấy dòng đầu tiên (Request Line)
            request_line = lines[0]
            print(request_line)
            method, path, http_version = request_line.split(" ")

            # Phân tích URL để lấy query parameters
            parsed_url = urlparse(path)
            query_params = parse_qs(parsed_url.query)
            
            if() # TODO: Check if a peer is in list
            # Create new peer
            peer_id = query_params['peer_id'][0]
            peer_ip = query_params['peer_ip'][0]
            peer_port = query_params['port'][0]

            # Append to list of peers
            peers.append({"peer_id": peer_id, "ip": peer_ip, "port": int(peer_port)})

            # Send response to peer
            if method != "GET":
                 conn.sendall("HTTP/1.1 100 NOT GET REQUEST\r\n".encode())
            elif query_params['info_hash'] == '':
                conn.sendall("HTTP/1.1 102 MISSING INFO HASH\r\n".encode())
            elif query_params['peer_id'] == '':
                conn.sendall("HTTP/1.1 103 MISSING PEER ID\r\n".encode())
            # elif len(query_params['info_hash'][0]) != 40:
            #     conn.sendall("HTTP/1.1 150 INVALID INFO HASH\r\n".encode())
            # elif len(query_params['peer_id'][0]) != 20:
            #     conn.sendall("HTTP/1.1 151 INVALID PEER ID\r\n".encode())
            else:
                params = {
                    "interval": 1800,
                    "peers": peers
                }
                if int(query_params['compact'][0]) == 1:
                    # Compact response (binary format)
                    compact_peers = b"".join(
                        socket.inet_aton(peer["ip"]) + peer["port"].to_bytes(2, "big")
                        for peer in peers
                    )
                    params[b"peers"] = compact_peers
                    # Non-compact response (list of dictionaries)
                    # Bencode response
                bencoded_response = bencodepy.encode(params)

                # Send HTTP response
                conn.sendall(
                    b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n" + bencoded_response
                )
            # TODO
            # new_peer = {"peer_id": peer_id, "port": port}
            # TODO: Add new peer to list
            break
        except Exception as e:
            print(e)
            print('Error occurred!')
            break
        time.sleep(5)
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
        nconn.join()
        time.sleep(5)
        break

if __name__ == "__main__":
    # hostname = socket.gethostname()
    hostip = get_host_default_interface_ip()
    port = 22236
    print("Listening on {}:{}".format(hostip, port))
    server_program(hostip, port)