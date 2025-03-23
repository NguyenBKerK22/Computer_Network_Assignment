import binascii
from threading import Thread
import socket
import constant
import time
import parsers
import node_info
import hashlib
import handshake


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

    # Compare info_hash
    torrent_info = parsers.parse_torrent("C:/Users/ADMIN/Documents/Zalo Received Files/Acer_Wallpaper_02_5000x2813.jpg.torrent")
    print(recv_message['info_hash'])
    print(torrent_info['info_hash'])
    if recv_message['info_hash'].hex() != torrent_info['info_hash']:
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
    bitfield_message = handshake.construct_bitfield_message(node_info.file_pieces)
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

    # Send choke message (initial state)
    # choke_message = b'\x00\x00\x00\x01\x00'
    # conn.sendall(choke_message)

    # TODO: Update am_interested status based on application logic
    # TODO: Communicate am_interested status to peer

