import binascii
from threading import Thread
import socket
import constant
import time
import parsers
import node_info
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
    handshake = conn.recv(constant.NUM_BYTE_HANDSHAKE)
    if not handshake:
        print(f"No handshake received from {addr}")
        conn.close()
        return

    # Parse handshake
    recv_message = parsers.parse_handshack_message(handshake)

    print(f"Received handshake from {addr}")
    print(f"pstrlen: {recv_message['pstrlen']}")
    print(f"pstr: {recv_message['pstr']}")
    print(f"info_hash: {recv_message['info_hash']}")
    print(f"peer_id: {recv_message['peer_id']}")

    # Compare info_hash
    torrent_info = parsers.parse_torrent("./Acer_Wallpaper_03_5000x2814.jpg.torrent")
    if recv_message['info_hash'] != torrent_info['info_hash']:
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
    conn.send(response_handshake)
    print(f"Sent response handshake to {addr}")

    # Initialize connection state
    am_interested = False
    am_choking = True
    peer_interested = False
    peer_choking = True

    # Send choke message (initial state)
    choke_message = b'\x00\x00\x00\x01\x00'
    conn.send(choke_message)

    # TODO: Update am_interested status based on application logic
    # TODO: Communicate am_interested status to peer

    def handle_peer_connection(conn, addr, am_interested, am_choking, peer_interested, peer_choking):
        # Keep-alive thread
        def keep_alive(conn):
            while True:
                time.sleep(120)
                try:
                    conn.send(b'\x00\x00\x00\x00')  # Keep-alive message
                    print(f"Sent keep-alive to {addr}")
                except:
                    print(f"Connection to {addr} lost")
                    break

        keep_alive_thread = Thread(target=keep_alive, args=(conn,))
        keep_alive_thread.daemon = True
        keep_alive_thread.start()

        # Message handling loop
        while True:
            try:
                message_length_bytes = conn.recv(4)
                if not message_length_bytes:
                    print(f"Connection closed by {addr}")
                    break

                message_length = int.from_bytes(message_length_bytes, 'big')

                if message_length == 0:
                    print(f"Received keep-alive from {addr}")
                    continue

                message_id = conn.recv(1)
                if not message_id:
                    print(f"Connection closed by {addr}")
                    break

                if message_length > 1:
                    payload = conn.recv(message_length - 1)
                else:
                    payload = b''
                print(f"Received message from {addr}: length={message_length}, id={message_id[0]}")

                def handle_message(message_id, payload, peer_choking, peer_interested, addr):
                    if message_id[0] == 0:  # Choke
                        peer_choking = True
                        print(f"Peer choked us")
                    elif message_id[0] == 1:  # Unchoke
                        peer_choking = False
                        print(f"Peer unchoked us")
                    elif message_id[0] == 2:  # Interested
                        peer_interested = True
                        print(f"Peer is interested")
                    elif message_id[0] == 3:  # Not Interested
                        peer_interested = False
                        print(f"Peer is not interested")
                    elif message_id[0] == 4:  # Have
                        piece_index = int.from_bytes(payload, 'big')
                        print(f"Peer has piece {piece_index}")
                    elif message_id[0] == 5:  # Bitfield
                        print(f"Peer bitfield: {binascii.hexlify(payload).decode()}")
                    elif message_id[0] == 6:  # Request
                        index = int.from_bytes(payload[:4], 'big')
                        begin = int.from_bytes(payload[4:8], 'big')
                        length = int.from_bytes(payload[8:], 'big')
                        print(f"Received request: index={index}, begin={begin}, length={length}")
                    elif message_id[0] == 7:  # Piece
                        index = int.from_bytes(payload[:4], 'big')
                        begin = int.from_bytes(payload[4:8], 'big')
                        block = payload[8:]
                        print(f"Received block: index={index}, begin={begin}, length={len(block)}")
                    elif message_id[0] == 8:  # Cancel
                        index = int.from_bytes(payload[:4], 'big')
                        begin = int.from_bytes(payload[4:8], 'big')
                        length = int.from_bytes(payload[8:], 'big')
                        print(f"Received cancel: index={index}, begin={begin}, length={length}")
                    # TODO: Communicate am_interested status to peer
                    return peer_choking, peer_interested

                peer_choking, peer_interested = handle_message(message_id, payload, peer_choking, peer_interested, addr)
            except Exception as e:
                print(f"Error handling message from {addr}: {e}")
                break

        conn.close()
        print(f"Connection to {addr} closed")

    handle_peer_connection(conn, addr, am_interested, am_choking, peer_interested, peer_choking)