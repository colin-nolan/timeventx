# Echo server program
import socket
import sys

HOST = "0.0.0.0"  # Symbolic name meaning all available interfaces
PORT = 50007  # Arbitrary non-privileged port

sa = (HOST, PORT)
sax = socket.getaddrinfo(*sa)[0][-1]

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(sax)
s.listen(1)

conn, addr = s.accept()

print("Connected by", addr)
while True:
    data = conn.recv(1024)
    if not data:
        break
    conn.send(data)
