import binascii
from threading import Thread
import socket
import constant
import time
import parsers
import node_info
import hashlib
import handshake
import math
import node
import os

#########################################
# Thread Server
#########################################
connected_peers = set()


def thread_server(host, port):
    print("Thread server listening on: {}:{}".format(host, port))

    serversocket = socket.socket()
    serversocket.bind((host, port))

    serversocket.listen(10)

    while True:
        conn, addr = serversocket.accept()
        nconn = Thread(target=new_message_incoming, args=(addr, conn))
        nconn.start()
        # nconn.join()


#########################################
# NEW SERVER INCOMING
#########################################
def new_message_incoming(addr, conn):
    # Receive Handshake
    handshake_message = conn.recv(constant.NUM_BYTE_HANDSHAKE)
    if not handshake_message:
        conn.close()
        return

    # Parse handshake
    recv_message = parsers.parse_handshack_message(handshake_message)

    # Find info_hashc
    match_found = False
    torrent_info = None
    for file_info in node_info.files:
        if recv_message['info_hash'].hex() == file_info['info_hash']:
            torrent_info = file_info
            match_found = True
            break
    if not match_found:
        conn.close()
        return
    file = open(os.path.join(f"./{node_info.node_folder}/files/", torrent_info["file_name"]), 'rb')
    # Send handshake back
    response_handshake = b''
    response_handshake += bytes([19])
    response_handshake += b'BitTorrent protocol'
    response_handshake += b'\x00' * 8
    response_handshake += binascii.unhexlify(torrent_info['info_hash'])
    response_handshake += node_info.PeerId.encode('utf-8')
    conn.sendall(response_handshake)

    # Send bitfield back
    bitfield_message = handshake.construct_bitfield_message(
        # Assume all pieces are available
        [1] * math.ceil(torrent_info["file_length"] / torrent_info["piece_length"])
    )
    if bitfield_message == b'':
        conn.close()
        return
    conn.sendall(bitfield_message)

    # Initialize connection state
    am_interested = False
    am_choking = True
    peer_interested = False
    peer_choking = True

    # TODO: create timeout for server
    while (1):
        try:
            message_length_bytes = conn.recv(4)
             # print(message_length_bytes)
            if not message_length_bytes:
                # node.peer_connections.pop(addr, None)
                return
            message_length = int.from_bytes(message_length_bytes, 'big')
            if message_length == 0:
                continue
            # receive message type
            message_type = conn.recv(1)
            if not message_type:
                break
            # receive payload
            if message_length > 1:
                payload = conn.recv(message_length - 1)
            else:
                payload = b''

            handshake.server_handle_message(message_type, payload, conn, addr, torrent_info, file)
        except socket.error as e:
            file.close()
            break


