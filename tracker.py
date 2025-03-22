import socket
from threading import Thread
from urllib.parse import urlparse, parse_qs
import bencodepy
import utils

# In-memory data structures
peers = []  # {peer_id: {"ip": str, "port": int, "files": [file_hashes]}}
tracker_id = "hehehehehehehehehehe"  # Unique tracker ID
torrents = {}


def new_connection(addr, conn):
    print(addr)
    while True:
        try:
            data = conn.recv(1024).decode()
            lines = data.split("\r\n")

            # Lấy dòng đầu tiên (Request Line)
            request_line = lines[0]
            method, path, http_version = request_line.split(" ")
            if method != "GET":
                conn.sendall("HTTP/1.1 100 NOT GET REQUEST\r\n".encode())
                return

            # Phân tích URL để lấy query parameters
            parsed_url = urlparse(path)
            query_params = parse_qs(parsed_url.query)

            # Exact value
            info_hash = query_params["info_hash"][0]
            peer_id = query_params["peer_id"][0]
            peer_port = int(query_params["port"][0])
            peer_ip = addr[0]
            uploaded = int(query_params["uploaded"][0])
            downloaded = int(query_params["downloaded"][0])
            left = int(query_params["left"][0])
            compact_mode = int(query_params.get("compact", [0])[0])

            # Check and send response to peer
            if query_params['info_hash'] == '':
                conn.sendall("HTTP/1.1 102 MISSING INFO HASH\r\n".encode())
            elif query_params['peer_id'] == '':
                conn.sendall("HTTP/1.1 103 MISSING PEER ID\r\n".encode())
            # elif len(query_params['info_hash'][0]) != 40:
            #     conn.sendall("HTTP/1.1 150 INVALID INFO HASH\r\n".encode())
            # elif len(query_params['peer_id'][0]) != 20:
            #     conn.sendall("HTTP/1.1 151 INVALID PEER ID\r\n".encode())
            else:
                if info_hash not in torrents:
                    torrents[info_hash] = []  # Initialize torrent peer list
                peer_list = torrents[info_hash]

                existing_peer = next((p for p in peer_list if p["peer_id"] == peer_id), None)
                if existing_peer:
                    existing_peer.update({
                        "peer_id": peer_id,
                        "ip": peer_ip,
                        "port": peer_port,
                        "uploaded": uploaded,
                        "downloaded": downloaded,
                        "left": left
                    })
                else:
                    # Prepare response
                    response_data = {"interval": 1800}

                    if compact_mode == 1:
                        compact_peers = b"".join(
                            socket.inet_aton(peer["ip"]) + peer["port"].to_bytes(2, "big")
                            for peer in peer_list
                        )
                        response_data[b"peers"] = compact_peers
                    else:
                        response_data[b"peers"] = [{"ip": p["ip"], "peer_id": p["peer_id"], "port": p["port"]} for p in
                                                   peer_list]

                    # Encode and send response
                    bencoded_response = bencodepy.encode(response_data)
                    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n" + bencoded_response)
                    print("HEHE")
                    conn.close()

                    peer_list.append({
                        "peer_id": peer_id,
                        "ip": peer_ip,
                        "port": peer_port,
                        "uploaded": uploaded,
                        "downloaded": downloaded,
                        "left": left
                    })

            break
        except Exception as e:
            print(e)
            print('Error occurred!')
            break


def tracker_server(host, port):
    serversocket = socket.socket()
    serversocket.bind((host, port))

    serversocket.listen(10)

    while True:
        print("Waiting for connection...")
        conn, addr = serversocket.accept()
        nconn = Thread(target=new_connection, args=(addr, conn))
        nconn.start()
        nconn.join()



if __name__ == "__main__":
    # hostname = socket.gethostname()
    hostip = utils.get_host_default_interface_ip()
    port = 22236
    print("Listening on {}:{}".format(hostip, port))
    tracker_server(hostip, port)