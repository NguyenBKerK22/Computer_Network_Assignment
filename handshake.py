import binascii
import utils
import node_info
import constant

diff_indexes = []
index = 0

def create_handshake_message(info_hash):
    handshake = b''
    handshake += bytes([19])
    handshake += b'BitTorrent protocol'
    handshake += b'\x00' * 8
    handshake += binascii.unhexlify(info_hash)
    handshake += node_info.PeerId.encode('utf-8')
    return handshake

def construct_choke_message():
    return b'\x00\x00\x00\x01\x00'

def construct_unchoke_message():
    return b'\x00\x00\x00\x01\x01'

def construct_interested_message():
    return b'\x00\x00\x00\x01\x02'

def construct_not_interested_message():
    return b'\x00\x00\x00\x01\x03'

def construct_have_message(piece_index):
    payload = piece_index.to_bytes(4, 'big')
    length = (1 + len(payload)).to_bytes(4, 'big')
    return length + b'\x04' + payload

def construct_bitfield_message(file_pieces):  # bitfield is a bytes object, bitmap of pieces
    if len(file_pieces) == 0:
        return b''

    bitfield = b''
    for i in range(0, len(file_pieces), 8):
        byte = 0
        for j in range(8):
            if i + j < len(file_pieces) and file_pieces[i + j] == 1:
                byte |= 1 << (7 - j)
        bitfield += byte.to_bytes(1, 'big')
    length = (1 + len(bitfield)).to_bytes(4, 'big')
    return length + b'\x05' + bitfield

def revert_bitfield_message(bitfield_bytes, total_pieces=None):
    # If total_pieces is provided, only that many bits will be returned.
    bits = []
    for byte in bitfield_bytes:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    if total_pieces is not None:
        bits = bits[:total_pieces]
    return bits

def construct_request_message(index, begin, length):
    payload = index.to_bytes(4, 'big') + begin.to_bytes(4, 'big') + length.to_bytes(4, 'big')
    length_bytes = (1 + len(payload)).to_bytes(4, 'big')
    return length_bytes + b'\x06' + payload

def construct_block_message(index, begin, block):
    payload = index.to_bytes(4, 'big') + begin.to_bytes(4, 'big') + block
    length_bytes = (1 + len(payload)).to_bytes(4, 'big')
    return length_bytes + b'\x07' + payload

def construct_cancel_message(index, begin, length):
    payload = index.to_bytes(4, 'big') + begin.to_bytes(4, 'big') + length.to_bytes(4, 'big')
    length_bytes = (1 + len(payload)).to_bytes(4, 'big')
    return length_bytes + b'\x08' + payload

def client_handle_message(socket, message_type, payload):
    global diff_indexes
    global index
    if message_type[0] == 0:  # Choke
        peer_choking = True
    elif message_type[0] == 1:  # Unchoke
        peer_choking = False
        print(f"Peer unchoked us")
    elif message_type[0] == 2:  # Interested
        peer_interested = True
        print(f"Peer is interested")
    elif message_type[0] == 3:  # Not Interested
        peer_interested = False
        print(f"Peer is not interested")
    elif message_type[0] == 5:  # Bitfield (server -> client)
        recv_file_pieces = revert_bitfield_message(payload)
        # compare with file_pieces
        diff_indexes = [i for i, (local, peer) in enumerate(zip(node_info.file_pieces, recv_file_pieces)) if local == 0 and peer == 1]
        # For example, request the first block of the piece:
        begin = 0
        block_length = 16384  # e.g., 16384 bytes (16KB)
        print(f"hihihihihi: {diff_indexes}")
        if diff_indexes:
            request_msg = construct_request_message(diff_indexes[index], begin, block_length)
            socket.sendall(request_msg)
            index = index + 1
        print(f"Sent request for piece {index} (offset {begin}, length {block_length})")

    elif message_type[0] == 7:  # block (server -> client)
        print("receive block")
        index_response = int.from_bytes(payload[:4], 'big')
        length = int.from_bytes(payload[4:8], 'big')
        block = payload[8:]
        utils.insert_piece_to_file(filename= "./hehe.jpg", piece_index = index_response, piece_data= block)
        if index != len(diff_indexes):
            begin = 0
            block_length = 16384  # e.g., 16384 bytes (16KB)
            request_msg = construct_request_message(diff_indexes[index], begin, block_length)
            index = index + 1
            socket.sendall(request_msg)
            print(f"Sent request XXXX for piece {index} (offset {begin}, length {block_length})")

def server_handle_message(message_type, payload, conn):
    if message_type[0] == 0:  # Choke
        peer_choking = True
        print(f"Peer choked us")
    elif message_type[0] == 1:  # Unchoke
        peer_choking = False
        print(f"Peer unchoked us")
    elif message_type[0] == 2:  # Interested
        peer_interested = True
        print(f"Peer is interested")
    elif message_type[0] == 3:  # Not Interested
        peer_interested = False
        print(f"Peer is not interested")
    elif message_type[0] == 4:  # Have (client -> server)
        piece_index = int.from_bytes(payload, 'big')
        print(f"[HAVE]")
    elif message_type[0] == 6:  # Request (client -> server)
        index = int.from_bytes(payload[:4], 'big')
        begin = int.from_bytes(payload[4:8], 'big')
        length = int.from_bytes(payload[8:], 'big')
        # read file from index * PIECE_SIZE to index * PIECE_SIZE + length
        with open(node_info.file_path, 'rb') as f:
            f.seek(index * constant.PIECE_SIZE + begin)
            block = f.read(length)

        block_message = construct_block_message(index, len(block), block)
        conn.sendall(block_message)
        f.close()
        print(f"[REQUEST]")
    elif message_type[0] == 8:  # Cancel (client -> server)
        index = int.from_bytes(payload[:4], 'big')
        begin = int.from_bytes(payload[4:8], 'big')
        length = int.from_bytes(payload[8:], 'big')
        print(f"[CANCEL]")