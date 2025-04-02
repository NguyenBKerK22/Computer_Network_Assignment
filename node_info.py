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

tracker_announce = "http://172.20.10.8:22236"

# http://192.168.31.147:22236
# http://10.230.117.212:22236
# http://192.168.31.77:22236
# http://10.0.120.133:22236
# http://192.168.1.105:22236

lockkkk = threading.Lock()
quit = threading.Lock()
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

status = 0

def setq_status(value):
    with quit:
        global status
        status = value
def getq_status():
    with quit:
        return status

com_lock = threading.Lock()
com = {
    "ip": ""
}

def set_com(key, value):
    with com_lock:
        global com
        com[key] = value

def get_com(key):
    with com_lock:
        return com.get(key)