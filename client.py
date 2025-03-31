import handshake
import math
import bencodepy
import requests
import  struct
import socket
import node_info
import constant
import parsers
import utils
import node
import time
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

def send_alert_to_tracker(interval):
    if interval > 0:
        print(f"⏳ Sending alert to tracker every {interval} seconds...")
        while True:
            # Gửi yêu cầu đến tracker
            response = send_request_to_tracker(node_info.torrent_info['announce'], node_info.torrent_info['info_hash'], node_info.torrent_info['file_length'], node_info.torrent_info['piece_length'], node_info.server_port, node_info.PeerId, node_info.peerip, "CC")
            if response is None:
                break
            time.sleep(interval)
