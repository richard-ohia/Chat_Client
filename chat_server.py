import socket
import threading
import time

HOST_NAME = "0.0.0.0"
PORT_NUMBER = 5378
BUFFER_SIZE = 64
MAX_NUM_CLIENTS = 100

connected_clients = []  # List to store connected client sockets
client_usernames = {}  # Dictionary to map client sockets to their usernames


def handle_client(client_socket):
    """
    This function handles communication with a client.
    It receives commands from the client and handles the commands.
    """
    try:
        if len(connected_clients) >= MAX_NUM_CLIENTS:
            client_socket.send("BUSY\n".encode())
            client_socket.close()
            return
        username_list = client_socket.recv(BUFFER_SIZE).decode(
            'ascii').strip().split()

        if len(username_list) > 2 or not username_list[1][0].isalpha():
            # This means that there is either space in the username
            # or doesn't start with a alphabetic character
            client_socket.send("BAD-RQST-BODY\n".encode())
            client_socket.close()
            return
        username = username_list[1]
        if username in client_usernames.values():
            client_socket.send("IN-USE\n".encode())
            client_socket.close()
            return
        client_usernames[client_socket] = username
        client_socket.send(f"HELLO {username}\n".encode())

        while True:
            # handle any length of message
            command = ""
            while not command.endswith("\n"):
                data = client_socket.recv(BUFFER_SIZE).decode('ascii')
                if not data:  # Empty message received, client has disconnected
                    break
                command += data

            if not command:  # Empty message received, client has disconnected
                break
            if command == "LIST\n":
                send_client_list(client_socket)
            elif command.startswith("SEND"):
                send_message(command, client_socket)
    except Exception:
        return

    # close connection and remove from list so it frees up space for same username
    client_socket.close()
    connected_clients.remove(client_socket)
    if client_socket in client_usernames:
        del client_usernames[client_socket]


def send_client_list(client_socket):
    """
    This function sends a list of online clients.
    """
    client_list = "[ "
    for username in client_usernames.values():
        client_list += username + ", "
    client_list = client_list[:len(client_list)-2] + " ]"
    client_socket.send(f"LIST-OK {client_list}\n".encode())


def send_message(message, sender_socket):
    """
    This function sends a message from one client to another.
    """
    message_parts = message.split()
    if len(message_parts) >= 3:
        receiver_username = message_parts[1]
        if receiver_username in client_usernames.values():
            for client_socket, username in client_usernames.items():
                if username == receiver_username:
                    forward_message = f"DELIVERY {client_usernames[sender_socket]} {' '.join(message_parts[2:])}\n"
                    client_socket.send(forward_message.encode())
                    # when sending to itself, it includes the SEND-OK response
                    # as part of the response so this helps seperate it
                    time.sleep(0.00005)

            sender_socket.send("SEND-OK\n".encode())
        else:
            sender_socket.send("BAD-DEST-USER\n".encode())
            return
    else:
        sender_socket.send("BAD-RQST-BODY\n".encode())
        return


def main():
    """
    This function starts the chat server and listens for incoming connections.
    It creates a new thread to handle each client connection.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST_NAME, PORT_NUMBER))
    server_socket.listen(64)
    print("Server running.")

    while True:
        client_socket, client_address = server_socket.accept()
        connected_clients.append(client_socket)
        address = str(client_address[0]) + ":" + str(client_address[1])
        print(f"new connection from {address}")
        client_thread = threading.Thread(
            target=handle_client, args=(client_socket,))
        client_thread.start()


main()
