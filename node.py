import socket
import time
import argparse
import threading
import math
import parsers
import utils
import client
import server
import node_info
import constant
import hashlib
import os
import handshake
from concurrent.futures import ThreadPoolExecutor

# Create peer infomation
peerip = utils.get_host_default_interface_ip()
peerid = node_info.PeerId

# Dictionary to store available pieces from peers
count = 0
peer_pieces = {}
peer_pieces_lock = threading.Lock()


def client_handshake_bitfield(serverip, serverport):
    print("hehe")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(serverip)
    print(serverport)
    client_socket.connect((serverip, serverport))

    client_socket.sendall(handshake.create_handshake_message(node_info.torrent_info['info_hash']))
    handshake_back = client_socket.recv(constant.NUM_BYTE_HANDSHAKE)
    if(handshake_back == b''):
        print("No handshake back received. Check for your info_hash")
        client_socket.close()
        return
    print("Handshake received")
    while True:
       message_length, message_type, payload = utils.receive_message(client_socket)
       print("Message length:", message_length)
       print("Message type:", message_type)
       recv_file_pieces = handshake.revert_bitfield_message(payload)
       with peer_pieces_lock:
           for piece_index, has_piece in enumerate(recv_file_pieces):
               if has_piece == 1:
                   if piece_index not in peer_pieces:
                       peer_pieces[piece_index] = []
                   peer_pieces[piece_index].append((serverip, serverport))
       break


if __name__ == "__main__":
    args_parser = argparse.ArgumentParser(
        prog='node',
        description='Node connect to predeclared server',
        epilog='<-- !! It requires the server is running and listening !!!'
    )
    args_parser.add_argument('--node-id', required=True)
    args_parser.add_argument('--server-port', required=True)
    args_parser.add_argument('--file-path', required=True)
    args = args_parser.parse_args()

    # NODE: Parse node id
    arr = ["node1", "node2", "node3", "node4", "node5"]
    node_info.node_folder = arr[int(args.node_id) - 1]

    # CLIENT: Parse torrent file
    node_info.file_path = args.file_path
    print(os.path.join(node_info.node_folder, args.file_path))
    # torrent_info = parsers.parse_torrent(os.path.join(node_info.node_folder, args.file_path))
    torrent_info = parsers.parse_torrent(f"./{node_info.node_folder}/torrents/{node_info.file_path}")
    print(len(torrent_info['pieces'].hex()))
    # CLIENT: save torrent information
    node_info.torrent_info = torrent_info
    # CLIENT: init downloaded pieces
    node_info.downloaded_pieces = [0] * math.ceil(torrent_info['file_length'] / torrent_info['piece_length'])
    
    # SERVER: load all files to mem
    def load_all_torrents(directory):
        for file in os.listdir(directory):
            torrent_info = parsers.parse_torrent(os.path.join(directory, file))
            node_info.files.append(torrent_info)
            
    load_all_files = load_all_torrents(f"./{node_info.node_folder}/torrents/")

    constant.PIECE_SIZE = torrent_info['piece_length']
    print(f"Piece size: {constant.PIECE_SIZE}")

    data_response = client.send_request_to_tracker(
        # 'http://192.168.31.147:22236',
        'http://10.0.135.103:22236',
        # 'http://192.168.1.106:22236',
        torrent_info['info_hash'],
        torrent_info['file_length'],
        torrent_info['piece_length'],
        int(args.server_port),
        peerid,
        peerip,
        "started"
    )

    # Get list of pieces
    MAX_THREADS = 10
    peers = parsers.parse_response(data_response)
    if peers:
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            handshakes = []
            for peer in peers:
                handshakes.append(
                    executor.submit(client_handshake_bitfield, peer[b'ip'], peer[b'port']))
            for hand in handshakes:
                hand.result()
    # After have a list of pieces
    # For client running
    # # servers = {}
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = []
        for piece_index, server_list in peer_pieces.items():
            if not server_list:
                continue
            serverip, serverport = server_list[0]  # Chọn server đầu tiên
            futures.append(executor.submit(client.thread_client_new, piece_index, serverip, serverport, piece_index))

        # Chờ tất cả các thread hoàn thành
        # for future in futures:
        #     future.result()

    # # For server running
    serverport = int(args.server_port)
    tserver = threading.Thread(target=server.thread_server, args=(peerip, serverport))
    tserver.start()
    tserver.join()
