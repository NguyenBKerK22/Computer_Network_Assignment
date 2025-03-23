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
import constant

def get_host_default_interface_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip
def generate_20_byte_peer_id():
    return str(str(uuid.uuid4())[:20])

def insert_piece_to_file(filename, piece_data, piece_index):
    try:
        with open(filename, 'w+b') as f:
            f.seek(piece_index * constant.PIECE_SIZE)
            f.write(piece_data)
            f.close()
    except Exception as e:
        print(f"An error occurred: {e}")