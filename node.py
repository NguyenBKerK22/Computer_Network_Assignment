# peer_connections = {}

# def select_best_peer():
#     best_peer = None
#     best_speed = 0
#     for addr, conn in peer_connections.items():
#         if hasattr(conn, 'peer_data') and 'upload_speed' in conn.peer_data and 'download_speed' in conn.peer_data:
#             combined_speed = conn.peer_data['upload_speed'] + conn.peer_data['download_speed']
#             if combined_speed > best_speed:
#                 best_speed = combined_speed
#                 best_peer = addr
#     return best_peer
import socket
import time
import argparse
from threading import Thread
import math
import uuid
import parsers
import utils
import client
import server
import node_info
import constant
import os
# Create peer infomation
peerip = utils.get_host_default_interface_ip()
peerid = node_info.PeerId

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
    torrent_info = parsers.parse_torrent(f"./{node_info.node_folder}/torrents/{node_info.file_path}")
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
        'http://10.0.120.133:22236',
        # 'http://192.168.1.106:22236',
        torrent_info['info_hash'],
        torrent_info['file_length'],
        torrent_info['piece_length'],
        int(args.server_port),
        peerid,
        peerip,
        "started"
    )
    peers = parsers.parse_response(data_response)

    if peers:
        print(str(peers[0][b'ip']) + " " + str(peers[0][b'port']))
        tclient = Thread(
            target=client.thread_client,
            args=(1, peers[0][b'ip'], peers[0][b'port']),
        )
        tclient.start()
        tclient.join()

    # For server running
    serverport = int(args.server_port)
    tserver = Thread(target=server.thread_server, args=(peerip, serverport))
    tserver.start()
    tserver.join()
