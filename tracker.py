import socket
from threading import Thread
from urllib.parse import urlparse, parse_qs
import bencodepy
import utils
import  time

peers = []

torrents = {}

def new_connection(addr, conn):
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
            event = query_params.get("event")
            # Check and send response to peer
            if query_params['info_hash'] == '':
                conn.sendall("HTTP/1.1 102 MISSING INFO HASH\r\n".encode())
            elif query_params['peer_id'] == '':
                conn.sendall("HTTP/1.1 103 MISSING PEER ID\r\n".encode())
            else:
                existing_peer = next((p for p in peers if p["peer_id"] == peer_id), None)
                current_time = time.time()
                if existing_peer and existing_peer["event"] != "completed":
                    # Cập nhật thời gian last_seen
                    if event == "stopped":
                        peers.remove(existing_peer)
                        return
                    existing_peer.update({
                        "peer_id": peer_id,
                        "ip": peer_ip,
                        "port": peer_port,
                        "uploaded": uploaded,
                        "downloaded": downloaded,
                        "left": left,
                        "event": event,
                        "last_seen": current_time
                    })
                    conn.close()
                else:
                    # Thêm peer mới vào danh sách
                    response_data = {"interval": 5}
                    if compact_mode == 1:
                        compact_peers = b"".join(
                            socket.inet_aton(peer["ip"]) + peer["port"].to_bytes(2, "big")
                            for peer in peers
                            if existing_peer and peer != existing_peer
                        )
                        response_data[b"peers"] = compact_peers
                    else:
                        response_data[b"peers"] = [{"ip": p["ip"], "peer_id": p["peer_id"], "port": p["port"]} for p in
                                                   peers]
                    bencoded_response = bencodepy.encode(response_data)
                    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n" + bencoded_response)
                    conn.close()
                    print(current_time)
                    peers.append({
                        "peer_id": peer_id,
                        "ip": peer_ip,
                        "port": peer_port,
                        "uploaded": uploaded,
                        "downloaded": downloaded,
                        "left": left,
                        "event": event,
                        "last_seen": current_time
                    })
                    print(f"Added peer: {peer_ip}:{peer_port} (ID: {peer_id})")
                break
            break
        except Exception as e:
            print(e)
            print('Error occurred!')
            break

def cleanup_inactive_peers():
    """Periodically remove peers that haven't reannounced within their interval."""
    while True:
        for peer in peers:
            # Remove peers that haven't reannounced within a grace period (e.g., interval + 300 seconds)
            current_time = time.time()
            if current_time - peer["last_seen"] > 20:
                peers.remove(peer)

        print(peers)
        time.sleep(5)  # run cleanup every 5 minutes


def tracker_server(host, port):
    serversocket = socket.socket()
    serversocket.bind((host, port))

    serversocket.listen(10)

    cleanup_thread = Thread(target=cleanup_inactive_peers, daemon=True)
    cleanup_thread.start()

    while True:
        conn, addr = serversocket.accept()
        nconn = Thread(target=new_connection, args=(addr, conn))
        nconn.start()
        # nconn.join()

if __name__ == "__main__":
    # hostname = socket.gethostname()
    hostip = utils.get_host_default_interface_ip()
    port = 22236
    print("Listening on {}:{}".format(hostip, port))
    tracker_server(hostip, port)