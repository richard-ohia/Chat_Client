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
import threading
import sys

HOST_NAME = "143.47.184.219"
PORT_NUMBER = 5378
BUFFER_SIZE = 2048


def handshake(socket_instance):
    """
    This function takes a socket object socket_instance as an argument and performs a handshake with the server. 
    It connects to the server using the HOST_NAME and PORT_NUMBER constants, 
    asks the user for a unique username, sends it to the server and receives a response from the server. 
    """
    socket_instance.connect((HOST_NAME, PORT_NUMBER))
    user_name = input("Please enter a user name: ")  # asks user for a username
    user_name = f"HELLO-FROM {user_name}\n"
    socket_instance.send(user_name.encode())
    buffer = socket_instance.recv(BUFFER_SIZE)
    return buffer


def handle_socket(socket_instance, stop_thread):
    """
    This function takes a socket object socket_instance as an argument and listens for any message from the server. 
    We use a timer to restart the loop to check our stop_thread flag 
    """
    socket_instance.settimeout(1.0)  # set the timeout to 1 second
    while not stop_thread.is_set():
        try:
            msg = socket_instance.recv(BUFFER_SIZE)
        except socket.timeout:
            continue  # timeout occurred, go back to the beginning of the loop
        msg_in_string = msg.decode('ascii')
        if msg_in_string.startswith("DELIVERY"):
            messages = msg_in_string.split(" ")
            print("\n" + messages[1] + " --> " + ' '.join(messages[2:]))
        else:
            print(server_output_to_msg(msg))
    return


def handle_user_input(socket_instance, stop_thread):
    """
    This function takes a socket object socket_instance as an argument and allows the user to interact with the server by entering commands. 
    The user can enter !quit to shutdown the client, 
    !who to list all currently logged-in users or @username message to send a message to another user. 
    The function sends the appropriate command to the server and receives a response from the server. 
    """
    while True:
        command = input()
        if (command == "!quit"):  # Lets the user shutdown the client by typing !quit
            stop_thread.set()
            break
        elif (command == "!who"):  # Lets the user list all currently logged-in users by typing !who
            user_list = "LIST\n"
            socket_instance.send(user_list.encode())
        # Lets the user send messages to other users by typing @username message
        elif (command.startswith("@")):
            message_list = command.split()
            user_name = message_list[0][1:]
            message = ' '.join(message_list[1:])
            send_message = f"SEND {user_name} {message}\n"
            socket_instance.send(send_message.encode())
        else:
            print(server_output_to_msg(None))  # if command is invalid, it returns none and `server_output_to_msg() prints the error `
    return


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
        return "Welcome online, " + username[1]


def main():
    socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    user = handshake(socket_instance)
    while (user == b"IN-USE\n"):
        print("User name already taken.")
        socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # if username is taken, user tries again
        user = handshake(socket_instance)
    print(server_output_to_msg(user))

    print("Please always enter your command in the empty new line: ")

    stop_thread = threading.Event()
    
    input_thread = threading.Thread(target=handle_user_input, args=(socket_instance, stop_thread))
    socket_thread = threading.Thread(target=handle_socket, args=(socket_instance, stop_thread))

    input_thread.start()
    socket_thread.start()


    input_thread.join()
    socket_thread.join()


    socket_instance.close()
    sys.exit() # Exit the program


main()
