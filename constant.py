import socket

NUM_BYTE_HANDSHAKE = 68

PIECE_SIZE = 2**4 * 1024 # 512KB

TIMEOUT_BITFIELD = 2  # seconds
TIMEOUT_REQUEST = 1  # seconds

MAX_RETRIES = 3  # Số lần thử lại nếu mất kết nối

NUM_OF_PIECES_IN_ONE_DAT = 20

NUM_OF_PIECE_TO_SELECT = 5