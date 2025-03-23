import socket
import time
import argparse
import mmap
from urllib.parse import urlparse, parse_qs
import bencodepy
import hashlib
import binascii
import requests
from requests import PreparedRequest
from threading import Thread
import math
import uuid
import parsers
import utils
import node_info
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

def construct_bitfield_message(bitfield): # bitfield is a bytes object, bitmap of pieces
    length = (1 + len(bitfield)).to_bytes(4, 'big')
    return length + b'\x05' + bitfield

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

def handle_message(message_type, payload):
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
        print(f"Peer has piece {piece_index}")
    elif message_type[0] == 5:  # Bitfield (server -> client)
        print(f"Peer bitfield: {binascii.hexlify(payload).decode()}")
    elif message_type[0] == 6:  # Request (client -> server)
        index = int.from_bytes(payload[:4], 'big')
        begin = int.from_bytes(payload[4:8], 'big')
        length = int.from_bytes(payload[8:], 'big')
        print(f"Received request: index={index}, begin={begin}, length={length}")
    elif message_type[0] == 7:  # block (server -> client)
        index = int.from_bytes(payload[:4], 'big')
        begin = int.from_bytes(payload[4:8], 'big')
        block = payload[8:]
        print(f"Received block: index={index}, begin={begin}, length={len(block)}")
    elif message_type[0] == 8:  # Cancel
        index = int.from_bytes(payload[:4], 'big')
        begin = int.from_bytes(payload[4:8], 'big')
        length = int.from_bytes(payload[8:], 'big')
        print(f"Received cancel: index={index}, begin={begin}, length={length}")