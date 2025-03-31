import utils

def renew_peer_id():
    global PeerId
    PeerId = utils.generate_20_byte_peer_id()
    return PeerId
data_file_path = "./3mb-examplefile-com.txt"
torrent_info = None
PeerId = renew_peer_id()
files = []

transfer_speed = {}
node_folder = None

bitfield_data = None # Bitfield data for the torrent

interval = 1 # Interval for tracker requests

server_port = None # Port for the server to listen on

peerip = None # IP address of the peer
