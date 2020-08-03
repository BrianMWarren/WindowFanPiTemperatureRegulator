import socket
import time

HOST = socket.gethostbyname('192.168.1.31')
print(HOST)
# HOST = 'WINDOWPIREPEAT1'  # The server's hostname or IP address
PORT = 6998        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    isOnB = bytes('OFF', encoding="utf-8")
    s.connect((HOST, PORT))
    s.sendall(isOnB)
    s.close()
    #data = s.recv(1024)