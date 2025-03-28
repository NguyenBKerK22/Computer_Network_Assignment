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

#########################################
# Thread Server
#########################################
def thread_server(host, port):
    print("Thread server listening on: {}:{}".format(host, port))

    serversocket = socket.socket()
    serversocket.bind((host, port))

    serversocket.listen(10)
    while True:
        conn, addr = serversocket.accept()
        print("Incoming connection from: {}".format(addr))
        nconn = Thread(target=new_message_incoming, args=(addr, conn))
        nconn.start()
        nconn.join()


#########################################
# NEW SERVER INCOMING
#########################################
def new_message_incoming(addr, conn):
    # Receive Handshake
    print(conn)
    handshake_message = conn.recv(constant.NUM_BYTE_HANDSHAKE)
    if not handshake_message:
        print(f"No handshake received from {addr}")
        conn.close()
        return

    # Parse handshake
    recv_message = parsers.parse_handshack_message(handshake_message)

    print(f"Received handshake from {addr}")
    print(f"pstrlen: {recv_message['pstrlen']}")
    print(f"pstr: {recv_message['pstr']}")
    print(f"info_hash: {recv_message['info_hash']}")
    print(f"peer_id: {recv_message['peer_id']}")

    # Find info_hash
    match_found = False
    torrent_info = None
    for file_info in node_info.files:
        if recv_message['info_hash'].hex() == file_info['info_hash']:
            torrent_info = file_info
            match_found = True
            break
    if not match_found:
        print("compare info_hash fail")
        print(f"Incorrect info_hash from {addr}")
        conn.close()
        return

    # Send handshake back
    response_handshake = b''
    response_handshake += bytes([19])
    response_handshake += b'BitTorrent protocol'
    response_handshake += b'\x00' * 8
    response_handshake += binascii.unhexlify(torrent_info['info_hash'])
    response_handshake += node_info.PeerId.encode('utf-8')
    conn.sendall(response_handshake)
    print(f"Sent response handshake to {addr}")

    # Send bitfield back
    bitfield_message = handshake.construct_bitfield_message(
        # Assume all pieces are available
        [1] * math.ceil(torrent_info["file_length"] / torrent_info["piece_length"]) 
    )
    if bitfield_message == b'':
        conn.close()
        return
    conn.sendall(bitfield_message)
    print(f"Sent bitfield to {addr}")

    # Initialize connection state
    am_interested = False
    am_choking = True
    peer_interested = False
    peer_choking = True

    while (1):
        message_length_bytes = conn.recv(4)
        if not message_length_bytes:
            print(f"Connection closed by server {addr}")
            return
        message_length = int.from_bytes(message_length_bytes, 'big')
        if message_length == 0:
            print(f"Received keep-alive from server {addr}")
            continue
        # receive message type
        message_type = conn.recv(1)
        if not message_type:
            print(f"Connection closed by server {addr}")
            break
        # receive payload
        if message_length > 1:
            payload = conn.recv(message_length - 1)
        else:
            payload = b''

        handshake.server_handle_message(message_type, payload, conn, torrent_info)

