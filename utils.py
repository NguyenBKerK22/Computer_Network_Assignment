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
import struct
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
        with open(filename, 'r+b') as f:
            f.seek(piece_index * constant.PIECE_SIZE)
            f.write(piece_data)
            f.close()
    except Exception as e:
        print(f"An error occurred: {e}")

def recv_exactly(sock, size):
    """ Nhận chính xác `size` byte từ socket """
    buffer = b''
    while len(buffer) < size:
        chunk = sock.recv(size - len(buffer))
        if not chunk:  # Nếu server đóng kết nối
            raise ConnectionError("Connection closed by peer")
        buffer += chunk
    return buffer

def receive_message(sock):
    """ Nhận một message theo format: [4 byte length] [1 byte type] [payload] """
    # Nhận 4 byte đầu tiên để lấy độ dài message
    raw_length = recv_exactly(sock, 4)
    message_length = struct.unpack(">I", raw_length)[0]  # Chuyển từ big-endian

    # Nhận 1 byte message type
    message_type = recv_exactly(sock, 1)

    # Nhận payload (nếu có)
    payload = recv_exactly(sock, message_length - 1) if message_length > 1 else b''

    return message_length, message_type[0], payload  # Trả về kiểu số nguyên + dữ liệu payload