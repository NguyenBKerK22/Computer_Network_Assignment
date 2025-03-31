import socket
import time
import argparse
import threading
import math
import uuid
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
from collections import defaultdict
import copy
# Create peer infomation
peerip = utils.get_host_default_interface_ip()
peerid = node_info.PeerId

# Dictionary to store available pieces from peers
# count = 0
peer_pieces = {}
peer_pieces_lock = threading.Lock()
downloading_lock = threading.Lock()

def select_servers(piece_map):
    server_pieces = defaultdict(list)

    # Gom nhóm pieces theo từng server
    for piece, servers in piece_map.items():
        for server in servers:
            server_pieces[server].append(piece)

    # Sắp xếp server theo số lượng pieces mà nó có (ưu tiên server có ít pieces nhất)
    sorted_servers = sorted(server_pieces.items(), key=lambda x: len(x[1]))

    # Kết quả: danh sách server và các pieces tương ứng
    return sorted_servers

def client_handshake_bitfield(serverip, serverport):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
                   if piece_index not in peer_pieces and (node_info.bitfield_data[node_info.torrent_info['info_hash']][piece_index] == 0):
                       peer_pieces[piece_index] = []
                   peer_pieces[piece_index].append((serverip, serverport, client_socket))
       break

def download_pieces(pieces, server_socket):
    # return array of pieces undownloaded
    undownloaded_pieces = copy.deepcopy(pieces)
    begin = 0
    block_length = constant.PIECE_SIZE  # 16KB mỗi lần tải

    for piece in pieces:
        if piece is not None:
            print(piece)
            attempt = 0
            while attempt < constant.MAX_RETRIES:
                request_msg = handshake.construct_request_message(piece, begin, block_length)
                
                try:
                    server_socket.sendall(request_msg)
                    message_length, message_type, payload = utils.receive_message(server_socket)
                    print("Message length request:", message_length)
                    print("Message type request:", message_type)
                    if handshake.client_handle_block(server_socket, message_type, payload):
                        undownloaded_pieces.remove(piece)
                        break  # Thành công, thoát vòng lặp thử lại
                    else:
                        attempt += 1

                except socket.timeout:
                    attempt += 1
                except (socket.error, ConnectionResetError, BrokenPipeError):
                    return undownloaded_pieces

    return undownloaded_pieces

def download_pieces_threaded(pieces, sock, ip, port, downloading):
    """Hàm chạy trên thread để tải dữ liệu từ peer"""
    with downloading_lock:
        pieces_to_download = [piece for piece in pieces if piece not in downloading]
        downloading.extend(pieces_to_download)

    if not pieces_to_download:
        print(f"Skipping {ip}:{port} as all pieces are being downloaded by other threads.")
        return []

    print(f"Starting download from {ip}:{port} for pieces: {len(pieces_to_download)}")
    undownloaded_pieces = download_pieces(pieces_to_download, sock)
    if undownloaded_pieces:
        print("Peer has disconnected")
    else:
        print(f"Finished downloading from {ip}:{port}")
    
    print(f"Undownloaded pieces: {len(undownloaded_pieces)}")
    with downloading_lock:
        for piece in undownloaded_pieces:
            if piece in downloading:
                downloading.remove(piece)

    return undownloaded_pieces

def start_downloading(sorted_data, selected_servers, downloading):
    """Hàm chính để tạo thread và quản lý tải dữ liệu."""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        
        server_index = 0
        while sorted_data and server_index < len(selected_servers):
            for index, value in sorted_data:
                if not value:
                    continue
                
                try:
                    ip, port, sock = value[server_index]
                    print(f"Get data at index[{server_index}]: {ip}:{port}")
                except IndexError:
                    print(f"No more servers available for this piece [{index}].")
                    continue
                
                for server_info, pieces in selected_servers:
                    if ip == server_info[0] and port == server_info[1]:
                        with downloading_lock:
                            pieces = [piece for piece in pieces if piece not in downloading]
                        if not pieces:
                            break
                        future = executor.submit(download_pieces_threaded, pieces, sock, ip, port, downloading)
                        futures.append(future.result())
                        break
                if future:
                    break

            # Reconstruct the code to avoid modifying sorted_data during iteration
            for future in futures:
                sorted_data = [piece_data for piece_data in sorted_data if piece_data[0] not in future]
            server_index += 1
            print("Switching to next server...")
            print("sorted_data:", 9999, "server_index:", server_index, "len(selected_servers):", len(selected_servers))
        if sorted_data:
            print("All online peer servers are disconnected or have no pieces. Please retry later !!!")
            return

def load_all_torrents(directory):
    for file in os.listdir(directory):
        torrent_info = parsers.parse_torrent(os.path.join(directory, file))
        node_info.files.append(torrent_info)

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
    arr = ["node1", "node2", "node3", "node4", "node5", "seed"]
    if int(args.node_id) != -1:
        node_info.node_folder = arr[int(args.node_id) - 1]
        # CLIENT: Parse torrent file
        node_info.file_path = args.file_path
        torrent_info = parsers.parse_torrent(f"./{node_info.node_folder}/torrents/{node_info.file_path}")
        # CLIENT: save torrent information
        node_info.torrent_info = torrent_info
        # CLIENT: init downloaded pieces
        node_info.bitfield_data[node_info.torrent_info['info_hash']] = [0] * math.ceil(torrent_info['file_length'] / torrent_info['piece_length'])

        load_all_files = load_all_torrents(f"./{node_info.node_folder}/torrents/")

        constant.PIECE_SIZE = node_info.torrent_info['piece_length']
        print(f"Piece size: {constant.PIECE_SIZE}")
    else:
        node_info.node_folder = arr[5]
        for file in os.listdir(f"./seed/torrents"):
            torrent_info = parsers.parse_torrent(f"./seed/torrents/{file}")
            node_info.bitfield_data[torrent_info['info_hash']] = [1] * math.ceil(torrent_info['file_length'] / torrent_info['piece_length'])
        load_all_files = load_all_torrents(f"./seed/torrents")

    # SERVER
    serverport = int(args.server_port)
    tserver = threading.Thread(target=server.thread_server, args=(peerip, serverport))
    tserver.start()

    data_response = client.send_request_to_tracker(
        'http://192.168.31.147:22236',
        # 'http://10.0.135.103:22236',
        # 'http://192.168.31.77:22236',
        # 'http://10.0.120.133:22236',
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

    # Downloading
    downloading = []
    # sort data by the number of elements in each list
    sorted_data = sorted(peer_pieces.items(), key=lambda x: len(x[1]))
    selected_servers = select_servers(peer_pieces)
    start_downloading(sorted_data, selected_servers, downloading)

    # For server running
    tserver.join()
