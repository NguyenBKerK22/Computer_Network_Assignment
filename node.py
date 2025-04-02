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
import glob
import random
import nodeUI



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
    
    try:
        client_socket.connect((serverip, serverport))
    except Exception as e:
        print(f"[EXCEPT] Connection error: {e}")
        client_socket.close()
        return
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
            attempt = 0
            while attempt < constant.MAX_RETRIES:
                request_msg = handshake.construct_request_message(piece, begin, block_length)
                
                try:
                    server_socket.sendall(request_msg)
                    message_length, message_type, payload = utils.receive_message(server_socket)
                    # print("Message length request:", message_length)
                    # print("Message type request:", message_type)
                    if handshake.client_handle_block(server_socket, message_type, payload):
                        undownloaded_pieces.remove(piece)
                        node_info.update_status(node_info.torrent_info['info_hash'], 
                                                "progress", 
                                                sum(node_info.bitfield_data[node_info.torrent_info['info_hash']]) / len(node_info.bitfield_data[node_info.torrent_info['info_hash']]) * 100
                                                )
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
                            pieces = [piece for piece in pieces if piece not in downloading][:5]
                        if not pieces:
                            break
                        future = executor.submit(download_pieces_threaded, pieces, sock, ip, port, downloading)
                        futures.append(future.result())
                        break
                # if future:
                #     break

                if len(value) != 0:
                    server_index = (server_index + 1) % len(value)
                    print("Switching to next server...")
                downloaded = sum(node_info.bitfield_data[node_info.torrent_info['info_hash']])
                if downloaded >= len(sorted_data):
                    break
                
            # Reconstruct the code to avoid modifying sorted_data during iteration
            for future in futures:
                sorted_data = [piece_data for piece_data in sorted_data if piece_data[0] in future]
            # server_index += 1
        if sorted_data:
            return
        else:
            dat_files = glob.glob(f"./{node_info.node_folder}/temp/*.dat")
            
            if not dat_files:
                print("No .dat files found to merge.")
            else:
                # Merge contents into a single file
                # check if file_name exists
                if os.path.exists(f"./{node_info.node_folder}/downloaded/{node_info.torrent_info['file_name']}"):
                    print(f"File {node_info.torrent_info['file_name']} already exists. I will delete it before merging.")
                    os.remove(f"./{node_info.node_folder}/downloaded/{node_info.torrent_info['file_name']}")
                    return
                # Create the directory if it doesn't exist
                os.makedirs(f"./{node_info.node_folder}/downloaded", exist_ok=True)
                # Merge all .dat files into one
                with open(f"./{node_info.node_folder}/downloaded/{node_info.torrent_info['file_name']}", "wb") as merged_file:
                    for dat_file in sorted(dat_files):
                        with open(dat_file, "rb") as f:
                            merged_file.write(f.read())
                        print(f"Appended {dat_file}")
                    merged_file.close()
                for dat_file in dat_files:
                    try:
                        os.remove(dat_file)
                    except Exception as e:
                        print(f"Failed to remove {dat_file}: {e}")
                print("All .dat files have been successfully merged into merged.dat")

def load_all_torrents(directory):
    for file in os.listdir(directory):
        torrent_info = parsers.parse_torrent(os.path.join(directory, file))
        node_info.files.append(torrent_info)

def checkquit():
    print("start check quit")
    while(1):
        if node_info.getq_status():
            print("Turn offf")
            client.send_request_to_tracker(
            node_info.tracker_announce,
            "aaa",
            "222",
            "123",
            int(node_info.server_port),
            node_info.PeerId,
            node_info.peerip,
            "stopped",
            0,
            0,
            7
            )
            break
        
            

def chay_thoi(filepath, nodeid, file_obj):
    print("CALL chay_thoi")
    arr = ["node1", "node2", "node3", "node4", "node5", "seed"]
    node_info.node_folder = arr[int(nodeid) - 1]
    # CLIENT: Parse torrent file
    node_info.file_path = filepath
    torrent_info = parsers.parse_torrent(f"./{node_info.node_folder}/torrents/{node_info.file_path}")
    # CLIENT: save torrent information
    node_info.torrent_info = torrent_info
    # CLIENT: init downloaded pieces
    node_info.bitfield_data[node_info.torrent_info['info_hash']] = [0] * math.ceil(torrent_info['file_length'] / torrent_info['piece_length'])

    # UI
    file_obj.append({"name": filepath, "progress": 0, "paused": False, "hash": torrent_info['info_hash']})
    node_info.append_status(torrent_info['info_hash'], {"progress": 0, "downloaded": 0, "total": 0})

    load_all_files = load_all_torrents(f"./{node_info.node_folder}/torrents/")

    constant.PIECE_SIZE = node_info.torrent_info['piece_length']
    print(f"Piece size: {constant.PIECE_SIZE}")
    
    data_response = client.send_request_to_tracker(
        node_info.tracker_announce,
        torrent_info['info_hash'],
        torrent_info['file_length'],
        torrent_info['piece_length'],
        int(node_info.server_port),
        node_info.PeerId,
        node_info.peerip,
        "started",
        0,
        0,
        math.ceil(torrent_info['file_length'] / torrent_info['piece_length'])
    )
    # INTERVAL
    node_info.interval = data_response[b'interval']
    talert = threading.Thread(target=client.send_alert_to_tracker, args=(node_info.interval,))
    talert.start()
    
    # CHECK QUIT
    tq = threading.Thread(target=checkquit, args=())
    tq.start()
    
    # Get list of pieces
    MAX_THREADS = 5
    peers = parsers.parse_response(data_response)

    if peers:
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            handshakes = []
            for peer in peers:
                handshakes.append(
                    executor.submit(client_handshake_bitfield, peer[b'ip'], peer[b'port']))
            for hand in handshakes:
                hand.result()

        downloading = []
        sorted_data = sorted(peer_pieces.items(), key=lambda x: len(x[1]))
        selected_servers = select_servers(peer_pieces)

        # clear temporaty folder before download
        dat_files = glob.glob(f"./{node_info.node_folder}/temp/*.dat")
        for dat_file in dat_files:
            os.remove(dat_file)
        start_downloading(sorted_data, selected_servers, downloading)

# if __name__ == "__main__":
#     # args_parser = argparse.ArgumentParser(
#     #     prog='node',
#     #     description='Node connect to predeclared server',
#     #     epilog='<-- !! It requires the server is running and listening !!!'
#     # )
#     # args_parser.add_argument('--node-id', required=True)
#     # args_parser.add_argument('--server-port', required=True)
#     # args_parser.add_argument('--file-path', required=True)
#     # args = args_parser.parse_args()

#     # NODE: Parse node id
    
#     sv_port = random.randint(10000, 65535)

#     # SERVER
#     node_info.server_port = sv_port
#     serverport = int(sv_port)
#     tserver = threading.Thread(target=server.thread_server, args=(peerip, serverport))
#     tserver.start()

#     # INTERVAL
#     # node_info.interval = data_response[b'interval']
#     # talert = threading.Thread(target=client.send_alert_to_tracker, args=(node_info.interval,))
#     # talert.start()
    
    
#     # For server running
#     # talert.join()

#     tserver.join()
