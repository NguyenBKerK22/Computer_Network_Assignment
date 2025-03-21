import socket
import time
import argparse
import mmap
from urllib.parse import urlparse, parse_qs
import bencodepy
import hashlib
import binascii
import requests
from requests import PreparedRequest
from threading import Thread

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

# Function to parse a magnet URI
def parse_magnet_uri(magnet_link):
    # Parse the magnet link
    parsed = urlparse(magnet_link)
    params = parse_qs(parsed.query)

    # Extract info hash
    info_hash = params.get('xt')[0].split(":")[-1]

    # Extract display name (optional)
    display_name = params.get('dn', ['Unknown'])[0]

    # Extract tracker URL (optional)
    tracker_url = params.get('tr', [''])[0]

    return info_hash, display_name, tracker_url

# Function to parse torrent file
def parse_torrent(file_path):
    with open(file_path, 'rb') as f:
        torrent_data = bencodepy.decode(f.read())
    #
    announce = torrent_data.get(b'announce', b'').decode()
    created_by = torrent_data.get(b'created by', b'').decode()
    creation_date = torrent_data.get(b'creation date', None)
    encoding = torrent_data.get(b'encoding', b'').decode()
    info = torrent_data.get(b'info', {})
    file_length = info.get(b'length', 0)
    file_name = info.get(b'name', b'').decode()
    info_bencoded = bencodepy.encode(info)
    info_hash = hashlib.sha1(info_bencoded).hexdigest()
    piece_length = info.get(b'piece length', 0)
    pieces = info.get(b'pieces', b'')
    return {
        "announce": announce,
        "created_by": created_by,
        "creation_date": creation_date,
        "encoding": encoding,
        "file_length": file_length,
        "file_name": file_name,
        "info_hash": info_hash,
        "piece_length": piece_length,
        "pieces": pieces
    }

# Function to parse response from tracker
def parse_response(content):
    return content.get('peers')

# Function to send request to tracker
def send_request_to_tracker(announce, info_hash, piece_length):
    # Các tham số gửi lên tracker
    params = {
        "info_hash": info_hash,
        "peer_id": "-UT360S-7p1....A3D9F0",
        "peer_ip": get_host_default_interface_ip(),
        "port": 6881,
        "uploaded": 0,
        "downloaded": 0,
        "left": piece_length,
        "compact": 1,
        "event": "started"
    }
    try:
        # Gửi request GET đến tracker với các tham số
        response = requests.get(announce, params=params, timeout=10)
        print(response)
        print(response.content)
        print(bencodepy.decode(response.content))
        # Kiểm tra nếu request thành công
        if response.status_code == 200:
            print(f"✅ Tracker Response Received:\n{response.text}")
            return response.content  # Trả về dữ liệu dạng binary
        else:
            print(f"⚠️ Tracker request failed with status {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"❌ Error connecting to tracker: {e}")
        return None

def new_server_incoming(addr, conn):
    print(addr)

def new_connection(addr, conn):
    print(conn)

#########################################
# Thread Server
#########################################
def thread_server(host, port):
    print("Thread server listening on: {}:{}".format(host, port))

    serversocket = socket.socket()
    serversocket.bind((host, port))

    serversocket.listen(10)
    while True:
        addr, conn = serversocket.accept()
        nconn = Thread(target=new_server_incoming, args=(addr, conn))
        nconn.start()
#########################################
# Thread Client
#########################################

def thread_client(id, serverip, serverport, peerip, peerport):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((serverip, serverport))
    client_socket.sendall("Hehe".encode('utf-8'))
    print('Thread ID {:d} connecting to {}:{:d}'.format(id, serverip, serverport))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='node',
        description='Node connect to predeclared server',
        epilog='<-- !! It requires the server is running and listening !!!'
    )

    parser.add_argument('--server-ip')
    parser.add_argument('--server-port', type=int)
    torrent_info = parse_torrent("C:/Users/ADMIN/Pictures/Acer/Acer_Wallpaper_03_5000x2814.jpg.torrent")
    data_response = send_request_to_tracker('http://192.168.31.147:22236', torrent_info['info_hash'], torrent_info['piece_length'])
    # list_response = parse_response(data_response)

    # parser.add_argument('--agent-path')

    # args = parser.parse_args()
    # serverip = args.server_ip
    # serverport = args.server_port
    # #agentpath = args.agent_path
    #
    # peerip = get_host_default_interface_ip()
    # peerport = 33357
    #
    # #tserver = Thread(target=thread_server, args=(peerip, 33357))
    # tclient = Thread(
    #     target=thread_client,
    #     args=(1, serverip, serverport, peerip, peerport)
    # )
    # #tagent = Thread(target=thread_agent, args=(2, agentpath))
    #
    # #tserver.start()
    # tclient.start()
    # tclient.join()
    #tagent.start()

    # Never completed
    #tserver.join()