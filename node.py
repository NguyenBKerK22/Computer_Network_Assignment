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
# Create peer infomation
peerip = utils.get_host_default_interface_ip()
peerid = node_info.PeerId

print(f"Peer ID: {peerid}")

# Parse torrent file
torrent_info = parsers.parse_torrent("C:/Users/ADMIN/Pictures/Acer/Acer_Wallpaper_02_5000x2813.jpg.torrent")
print(torrent_info)
node_info.file_pieces = [1] * math.ceil(torrent_info["file_length"] / torrent_info["piece_length"])
print(node_info.file_pieces)
constant.PIECE_SIZE = torrent_info['piece_length']
if __name__ == "__main__":
    args_parser = argparse.ArgumentParser(
        prog='node',
        description='Node connect to predeclared server',
        epilog='<-- !! It requires the server is running and listening !!!'
    )
    args_parser.add_argument('--server-port', required=True)
    args = args_parser.parse_args()

    data_response = client.send_request_to_tracker(
        'http://192.168.31.147:22236',
        #'http://10.0.239.2:22236',
        # 'http://192.168.1.105:22236',
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
            args=(1, peers[0][b'ip'], peers[0][b'port'], torrent_info),
        )
        tclient.start()
        tclient.join()

    # For server running
    serverport = int(args.server_port)
    tserver = Thread(target=server.thread_server, args=(peerip, serverport))
    tserver.start()
    tserver.join()
