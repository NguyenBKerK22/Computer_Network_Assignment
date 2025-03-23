import handshake
import math
import bencodepy
import requests
import socket
import node_info
import constant
import parsers
import utils
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
    state = 1
    list_piece_data = []
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((serverip, serverport))

    client_socket.sendall(handshake.create_handshake_message(torrent_info['info_hash']))
    handshake_back = client_socket.recv(constant.NUM_BYTE_HANDSHAKE)
    if(handshake_back == b''):
        print("No handshake back received. Check for your info_hash")
        client_socket.close()
        return
    while True:
        # recv message length
        message_length_bytes = client_socket.recv(4)
        if not message_length_bytes:
            print(f"Connection closed by server {serverip}")
            return
        message_length = int.from_bytes(message_length_bytes, 'big')
        if message_length == 0:
            print(f"Received keep-alive from server {serverip}")
            continue
        # receive message type
        message_type = client_socket.recv(1)
        if not message_type:
            print(f"Connection closed by server {serverip}")
            break
        # receive payload
        if message_length > 1:
            payload = client_socket.recv(message_length - 1)
        else:
            payload = b''
            break
        handshake.client_handle_message(client_socket, message_type, payload)
        
    
