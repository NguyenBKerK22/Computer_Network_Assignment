import utils

PeerId = utils.generate_20_byte_peer_id()

def renew_peer_id():
    global PeerId
    PeerId = utils.generate_20_byte_peer_id()
    return PeerId