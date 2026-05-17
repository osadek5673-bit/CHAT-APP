import socket
import threading

HOST = '0.0.0.0'  
PORT = 7000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

clients = []

def broadcast(data, sender_socket):
    
    for client in clients:
        if client != sender_socket:
            try:
                client.sendall(data)
            except:
                if client in clients:
                    clients.remove(client)
                client.close()

def handle_client(client_socket):
    
    while True:
        try:
        
            data = client_socket.recv(4096)
            if not data:
                break
            broadcast(data, client_socket)
        except:
            break
            
    if client_socket in clients:
        clients.remove(client_socket)
    client_socket.close()

print(f"Server is running on port {PORT}...")
while True:
    client_socket, address = server.accept()
    print(f"Connected with {address}")
    clients.append(client_socket)
    thread = threading.Thread(target=handle_client, args=(client_socket,))
    thread.start()