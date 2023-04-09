import socket
import select
import sys

HOST_NAME = "143.47.184.219"
PORT_NUMBER = 5378
BUFFER_SIZE = 2048


def handshake(socket_instance):
    socket_instance.connect((HOST_NAME, PORT_NUMBER))
    user_name = input("Please enter a user name: ")
    user_name = f"HELLO-FROM {user_name}\n"
    name_bytes_sent = socket_instance.send(user_name.encode())
    buffer = socket_instance.recv(BUFFER_SIZE)
    return buffer


def handle_user_input(command, socket_instance):
    if (command == "!quit"):  # Lets the user shutdown the client by typing !quit
        return sys.exit(1)
    elif (command == "!who"):  # Lets the user list all currently logged-in users by typing !who
        user_list = "LIST\n"
        list_bytes_sent = socket_instance.send(user_list.encode())
    # Lets the user send messages to other users by typing @username message
    elif (command.startswith("@")):
        message_list = command.split()
        user_name = message_list[0][1:]
        message = message_list[1].strip("\n")
        send_message = f"SEND {user_name} {message}\n"
        list_bytes_sent = socket_instance.send(send_message.encode())
    else:
        return None
    buffer = socket_instance.recv(BUFFER_SIZE)
    return buffer


def server_output_to_msg(server_output):
    if server_output is None:
        return "Error with given command or server response."
    server_output = server_output.decode('ascii')
    if server_output == "SEND-OK\n":
        return "Message sent successfully!"
    elif server_output == "BAD-DEST-USER\n":
        return "User is currently not online or doesn't exist."
    elif server_output == "BUSY\n":
        return "Server is currently busy!"
    elif server_output == "BAD-RQST-HDR\n":
        return "Request header is invalid."
    elif server_output == "BAD-RQST-BODY\n":
        return "Request body is invalid."
    elif server_output.startswith("LIST-OK"):
        return server_output.strip("LIST-OK")
    elif server_output.startswith("HELLO"):
        username = server_output.split(" ")
        return "Welcome online " + username[1]


def main():
    socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    user = handshake(socket_instance)
    while (user == b"IN-USE\n"):
        print("User name already taken.")
        socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        user = handshake(socket_instance)
    print("Please always enter your command in the empty new line: ")
    sockets = [socket_instance, sys.stdin]
    while True:
        read_message, write_message, error = select.select(
            sockets, [], [], 0.5)
        if error:
            print(f"Error: {error}")
        if sys.stdin in read_message:
            user_command = input()
            res = handle_user_input(user_command, socket_instance)
            print(server_output_to_msg(res))
        for sock in read_message:
            if sock == socket_instance:
                msg = sock.recv(BUFFER_SIZE).decode('ascii')
                if msg.startswith("DELIVERY"):
                    messages = msg.split(" ")
                    print("\n" + messages[1] + " --> " + messages[2])


main()
