"""
The application must:

Implement the chat protocol described in Appendix A of the Lab Guide.
Connect to the chat server and let the user log in using a unique name. ~ Ask for another name if the chosen name is already taken.
Let the user shutdown the client by typing !quit.
Let the user list all currently logged-in users by typing !who.
Let the user send messages to other users by typing @username message.
Receive messages from other users and display them to the user.

@authors Richard Ohia and Yonas Gebregziabher 
"""

import socket
import select
import sys

HOST_NAME = "143.47.184.219"
PORT_NUMBER = 5378
BUFFER_SIZE = 2048


def handshake(socket_instance):
    socket_instance.connect((HOST_NAME, PORT_NUMBER))
    user_name = input("Please enter a user name: ")  # asks user for a username
    user_name = f"HELLO-FROM {user_name}\n"
    name_bytes_sent = socket_instance.send(user_name.encode())
    buffer = socket_instance.recv(BUFFER_SIZE)
    return buffer


def handle_user_input(command, socket_instance):
    if (command == "!quit"):  # Lets the user shutdown the client by typing !quit
        return sys.exit(1)
    elif (command == "!who"):  # Lets the user list all currently logged-in users by typing !who
        user_list = "LIST\n"
        socket_instance.send(user_list.encode())
    # Lets the user send messages to other users by typing @username message
    elif (command.startswith("@")):
        message_list = command.split()
        user_name = message_list[0][1:]
        message = message_list[1].strip("\n")
        send_message = f"SEND {user_name} {message}\n"
        socket_instance.send(send_message.encode())
    else:
        return None  # if command is invalid, it returns none and `server_output_to_msg() prints the error `
    buffer = socket_instance.recv(BUFFER_SIZE)
    return buffer


def server_output_to_msg(server_output):
    """
    This function translates server codes into user friendly 
    messages to be printed in the terminal.
    """
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
        # if username is taken, user tries again
        user = handshake(socket_instance)
    print("Please always enter your command in the empty new line: ")
    sockets = [socket_instance, sys.stdin]  # processes to track

    # select package allows us to monitor sockets and io input and allows us
    # to access their written/readable values. This makes it easy to listen to
    # incoming messages but also when a user types a command.
    while True:
        # program loops indefinetly until user terminates with `!quit` command.
        read_message, write_message, error = select.select(
            sockets, [], [])
        if error:
            print(f"Error: {error}")
        if sys.stdin in read_message:  # looks for user command inputs
            user_command = input()
            res = handle_user_input(user_command, socket_instance)
            print(server_output_to_msg(res))
        for sock in read_message:
            if sock == socket_instance:
                # the incoming message, that comes in bytes, is then decoded into ascci so that
                # the user can read the message they've gotten. It is displayed in this format.
                # [sender] --> [msg]
                msg = sock.recv(BUFFER_SIZE).decode('ascii')
                if msg.startswith("DELIVERY"):
                    messages = msg.split(" ")
                    print("\n" + messages[1] + " --> " + messages[2])


main()
