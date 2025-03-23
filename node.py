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

# Create peer infomation
peerip = utils.get_host_default_interface_ip()
peerid = node_info.PeerId
print(f"Peer ID: {peerid}")

# Parse torrent file
torrent_info = parsers.parse_torrent("./Acer_Wallpaper_03_5000x2814.jpg.torrent")

if __name__ == "__main__":
    args_parser = argparse.ArgumentParser(
        prog='node',
        description='Node connect to predeclared server',
        epilog='<-- !! It requires the server is running and listening !!!'
    )
    args_parser.add_argument('--server-port', required=True)
    args = args_parser.parse_args()

    data_response = client.send_request_to_tracker(
        'http://192.168.31.77:22236',
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
