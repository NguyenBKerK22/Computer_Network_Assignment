import utils

def renew_peer_id():
    global PeerId
    PeerId = utils.generate_20_byte_peer_id()
    return PeerId
file_path = "./Acer_Wallpaper_02_5000x2813.jpg"
PeerId = renew_peer_id()
file_pieces = []