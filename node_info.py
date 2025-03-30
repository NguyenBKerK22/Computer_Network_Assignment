import utils

def renew_peer_id():
    global PeerId
    PeerId = utils.generate_20_byte_peer_id()
    return PeerId
data_file_path = "./3mb-examplefile-com.txt"
torrent_info = None
PeerId = renew_peer_id()
files = []
downloaded_pieces = [] # List of pieces that have been downloaded
transfer_speed = {}
node_folder = None
