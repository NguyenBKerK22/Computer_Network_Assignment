import binascii
import utils
import node_info
import constant
import os
import hashlib
import mmap
import time
diff_indexes = []
index = 0
f = None
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

def client_handle_block(socket, message_type, payload):
    index_response = int.from_bytes(payload[:4], 'big')
    length = int.from_bytes(payload[4:8], 'big')
    block = payload[8:]
    # print("Index:", index_response)
    # print("Length:", length)
    if node_info.torrent_info['pieces'][index_response * 20 : index_response * 20 + 20] == hashlib.sha1(block).digest():
        
        range_min = index_response // constant.NUM_OF_PIECES_IN_ONE_DAT * constant.NUM_OF_PIECES_IN_ONE_DAT
        range_max = (index_response // constant.NUM_OF_PIECES_IN_ONE_DAT + 1) * constant.NUM_OF_PIECES_IN_ONE_DAT - 1
        offset = index_response % constant.NUM_OF_PIECES_IN_ONE_DAT
        file_name_dat = f"./{node_info.node_folder}/temp/piece{range_min}_{range_max}.dat"
        
        # print("Range min:", range_min)
        # print("Range max:", range_max)
        # print("File name:", file_name_dat)
        # print("Offset:", offset)
        
        # check if the folder is already created
        if not os.path.exists(f"./{node_info.node_folder}/temp"):
            os.makedirs(f"./{node_info.node_folder}/temp")
        
        utils.insert_piece_to_file(filename= file_name_dat, piece_index = offset, piece_data = block)
        
        # utils.insert_piece_to_file(filename= f"./{node_info.node_folder}/downloaded/{node_info.torrent_info['file_name']}", piece_index = index_response, piece_data= block)
        
        # utils.map_piece_to_file(filename= f"./{node_info.node_folder}/downloaded/{node_info.torrent_info['file_name']}", piece_index = index_response, piece_data= block)
        node_info.bitfield_data[node_info.torrent_info['info_hash']][index_response] = 1
        downloaded = sum(node_info.bitfield_data[node_info.torrent_info['info_hash']])
        left = len(node_info.bitfield_data[node_info.torrent_info['info_hash']]) - downloaded
        percent = int(downloaded / (downloaded + left) * 100)
        print("Downloaded percent: {}%".format(percent))
        return True
    else:
        return False
def server_handle_message(message_type, payload, conn, addr, torrent_info, file):
    if message_type[0] == 4:  # Have (client -> server)
        piece_index = int.from_bytes(payload, 'big')
    elif message_type[0] == 6:  # Request (client -> server)
        global f
        index_response = int.from_bytes(payload[:4], 'big')
        begin = int.from_bytes(payload[4:8], 'big')
        length = int.from_bytes(payload[8:], 'big')
        file.seek(index_response * length + begin)
        block = file.read(length)

        block_message = construct_block_message(index_response, len(block), block)
        conn.sendall(block_message)
    elif message_type[0] == 8:  # Cancel (client -> server)
        index = int.from_bytes(payload[:4], 'big')
        begin = int.from_bytes(payload[4:8], 'big')
        length = int.from_bytes(payload[8:], 'big')