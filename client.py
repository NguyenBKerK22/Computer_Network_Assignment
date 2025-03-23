import handshake
import math
import bencodepy
import requests
import socket
import node_info
import constant
# Function to send request to tracker

def send_request_to_tracker(announce, info_hash, file_length, piece_length, port, peerid, peerip, event):
    # Các tham số gửi lên tracker
    params = {
        "info_hash": info_hash,
        "peer_id": peerid,
        "peer_ip": peerip,
        "port": port,
        "uploaded": 0,
        "downloaded": 0,
        "left": math.ceil(file_length / piece_length),
        "compact": 0,
        "event": event
    }
    print(peerip)
    try:
        response = requests.get(announce, params=params, timeout=10)
        if response.status_code == 200:
            print(f"✅")
            decoded = bencodepy.decode(response.content)
            if params['compact'] == 1:
                print(decoded[b'peers'].hex())
            else:
                print(decoded[b'peers'])
            return decoded  # Trả về dữ liệu dạng binary
        else:
            print(f"⚠️ Tracker request failed with status {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"❌ Error connecting to tracker: {e}")
        return None

def thread_client(id, serverip, serverport, torrent_info):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((serverip, serverport))

    client_socket.sendall(handshake.create_handshake_message(torrent_info['info_hash']))
    client_socket.recv(constant.HANDSHAKE_MESSAGE_LENGTH)

    
    print('Thread ID {:d} connecting to {}:{:d}'.format(id, serverip, serverport))
