import utils
import threading

torrent_info = None
PeerId = None
files = []

transfer_speed = {}
node_folder = None

bitfield_data = {} # Bitfield data for the torrent

interval = 1 # Interval for tracker requests

server_port = None # Port for the server to listen on

peerip = None # IP address of the peer

tracker_announce = "http://192.168.1.105:22236"



lockkkk = threading.Lock()
node_status = {
    'hash-abc-defgh': {
        "progress": 0,
        "downloaded": 0,
        "total": 0,
    }
    # add other properties as needed
}

def append_status(key, value):
    with lockkkk:
        if key not in node_status:
            node_status[key] = {
                "progress": 0,
                "downloaded": 0,
                "total": 0,
            }

def update_status(key, key2, value):
    with lockkkk:
        node_status[key][key2] = value

def get_status(key):
    with lockkkk:
        return node_status.get(key)

# http://192.168.31.147:22236
# http://10.230.77.196:22236
# http://192.168.31.77:22236
# http://10.0.120.133:22236
# http://192.168.1.105:22236
