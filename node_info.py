import utils

def renew_peer_id():
    global PeerId
    PeerId = utils.generate_20_byte_peer_id()
    return PeerId
file_path = "./3mb-examplefile-com.txt"
PeerId = renew_peer_id()
file_pieces = []