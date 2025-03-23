from urllib.parse import urlparse, parse_qs
import bencodepy
import hashlib
def parse_magnet_uri(magnet_link):
    # Parse the magnet link
    parsed = urlparse(magnet_link)
    params = parse_qs(parsed.query)

    # Extract info hash
    info_hash = params.get('xt')[0].split(":")[-1]

    # Extract display name (optional)
    display_name = params.get('dn', ['Unknown'])[0]

    # Extract tracker URL (optional)
    tracker_url = params.get('tr', [''])[0]

    return info_hash, display_name, tracker_url

def parse_torrent(file_path):
    with open(file_path, 'rb') as f:
        torrent_data = bencodepy.decode(f.read())
    #
    announce = torrent_data.get(b'announce', b'').decode()
    created_by = torrent_data.get(b'created by', b'').decode()
    creation_date = torrent_data.get(b'creation date', None)
    encoding = torrent_data.get(b'encoding', b'').decode()
    info = torrent_data.get(b'info', {})
    file_length = info.get(b'length', 0)
    file_name = info.get(b'name', b'').decode()
    info_bencoded = bencodepy.encode(info)
    info_hash = hashlib.sha1(info_bencoded).hexdigest()
    piece_length = info.get(b'piece length', 0)
    pieces = info.get(b'pieces', b'')
    return {
        "announce": announce,
        "created_by": created_by,
        "creation_date": creation_date,
        "encoding": encoding,
        "file_length": file_length,
        "file_name": file_name,
        "info_hash": info_hash,
        "piece_length": piece_length,
        "pieces": pieces
    }
def parse_response(content):
    return content[b'peers']

def parse_handshack_message(message):
    recv_pstrlen = message[0]
    recv_pstr = message[1:1 + recv_pstrlen].decode()
    recv_reserved = message[1 + recv_pstrlen:9 + recv_pstrlen]
    recv_info_hash = message[9 + recv_pstrlen:29 + recv_pstrlen]
    recv_peer_id = message[29 + recv_pstrlen:].decode()
    return {
        "pstrlen": recv_pstrlen,
        "pstr": recv_pstr,
        "reserved": recv_reserved,
        "info_hash": recv_info_hash,
        "peer_id": recv_peer_id
    }