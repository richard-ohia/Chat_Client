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
PORT_NUMBER = 5382
BUFFER_SIZE = 64

DROP = 0
FLIP = 0
BURST = 0
BURST_LEN_LOW = 0
BURST_LEN_HIGH = 3
DELAY = 0
DELAY_LEN_LOW = 0
DELAY_LEN_HIGH = 5


def handshake(socket_instance):
    """
    This function takes a socket object socket_instance as an argument and performs a handshake with the server. 
    It connects to the server using the HOST_NAME and PORT_NUMBER constants, 
    asks the user for a unique username, sends it to the server and receives a response from the server. 
    """
    user_name = input("Please enter a user name: ")  # asks user for a username
    user_name = f"HELLO-FROM {user_name}\n"
    socket_instance.sendto(user_name.encode(), (HOST_NAME, PORT_NUMBER))
    buffer = socket_instance.recvfrom(BUFFER_SIZE)
    return buffer


def get_value_of_config(socket_instance, setting_name):
    command = f"GET {setting_name}\n"
    socket_instance.sendto(command.encode(), (HOST_NAME, PORT_NUMBER))
    response = socket_instance.recvfrom(BUFFER_SIZE)
    return f"{setting_name} -> {response[0].decode('ascii')}"


def configure_server(socket_instance, set_drop=DROP, set_flip=FLIP, set_burst=BURST, set_low_burst_len=BURST_LEN_LOW, set_upper_burst_len=BURST_LEN_HIGH, set_delay=DELAY, set_low_delay_len=DELAY_LEN_LOW, set_upper_delay_len=DELAY_LEN_HIGH):
    # conditional check to prevent redudant server calls
    if set_drop != DROP:
        command = f"SET DROP {str(set_drop)}\n"
        socket_instance.sendto(command.encode(), (HOST_NAME, PORT_NUMBER))
        response = socket_instance.recvfrom(BUFFER_SIZE)
        if (response[0].decode('ascii') == "SET-OK\n"):
            print(f"Successfully set DROP to {set_drop}")
        else:
            print("Failed to configure DROP in the server.")
    if set_flip != FLIP:
        command = f"SET FLIP {str(set_flip)}\n"
        socket_instance.sendto(command.encode(), (HOST_NAME, PORT_NUMBER))
        response = socket_instance.recvfrom(BUFFER_SIZE)
        if (response[0].decode('ascii') == "SET-OK\n"):
            print(f"Successfully set FLIP to {set_flip}")
        else:
            print("Failed to configure FLIP in the server.")
    if set_burst != BURST:
        command = f"SET BURST {str(set_burst)}\n"
        socket_instance.sendto(command.encode(), (HOST_NAME, PORT_NUMBER))
        response = socket_instance.recvfrom(BUFFER_SIZE)
        if (response[0].decode('ascii') == "SET-OK\n"):
            print(f"Successfully set BURST to {set_burst}")
        else:
            print("Failed to configure BURST in the server.")
    if set_delay != DELAY:
        command = f"SET BURST {str(set_delay)}\n"
        socket_instance.sendto(command.encode(), (HOST_NAME, PORT_NUMBER))
        response = socket_instance.recvfrom(BUFFER_SIZE)
        if (response[0].decode('ascii') == "SET-OK\n"):
            print(f"Successfully set DELAY to {set_delay}")
        else:
            print("Failed to configure DELAY in the server.")
    if set_low_burst_len != BURST_LEN_LOW or set_upper_burst_len != BURST_LEN_HIGH:
        command = f"SET BURST-LEN {str(set_low_burst_len)} {str(set_upper_burst_len)} \n"
        socket_instance.sendto(command.encode(), (HOST_NAME, PORT_NUMBER))
        response = socket_instance.recvfrom(BUFFER_SIZE)
        if (response[0].decode('ascii') == "SET-OK\n"):
            print(
                f"Successfully set BURST-LEN to {set_low_burst_len} - {set_upper_burst_len}")
        else:
            print("Failed to configure BURST-LEN in the server.")
    if set_low_delay_len != DELAY_LEN_LOW or set_upper_delay_len != DELAY_LEN_HIGH:
        command = f"SET DELAY-LEN {str(set_low_delay_len)} {str(set_upper_delay_len)} \n"
        socket_instance.sendto(command.encode(), (HOST_NAME, PORT_NUMBER))
        response = socket_instance.recvfrom(BUFFER_SIZE)
        if (response[0].decode('ascii') == "SET-OK\n"):
            print(
                f"Successfully set DELAY-LEN to {set_low_delay_len} - {set_upper_delay_len}")
        else:
            print("Failed to configure DELAY-LEN in the server.")


def handle_socket(socket_instance, stop_thread):
    """
    This function takes a socket object socket_instance as an argument and listens for any message from the server. 
    We use a timer to restart the loop to check our stop_thread flag 
    """
    socket_instance.settimeout(1.0)  # set the timeout to 1 second
    while not stop_thread.is_set():
        final_msg = ""
        msg = None
        try:
            msg = socket_instance.recvfrom(BUFFER_SIZE)
            decoded = msg[0].decode("ascii")
            while (len(decoded) >= 1):
                if (decoded[-1] == "\n"):
                    final_msg += decoded
                    break
                final_msg += decoded
                msg = socket_instance.recvfrom(
                    BUFFER_SIZE)
                decoded = msg.decode("ascii")

        except socket.timeout:
            continue  # timeout occurred, go back to the beginning of the loop
        if final_msg.startswith("DELIVERY"):
            messages = final_msg.split(" ")
            print("\n" + messages[1] + " --> " + ' '.join(messages[2:]))
        else:
            print(server_output_to_msg(final_msg))
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
            socket_instance.sendto(
                user_list.encode(), (HOST_NAME, PORT_NUMBER))
        elif (command.startswith("!get")):
            print(f"Command is {command}")
            server_config = get_value_of_config(
                socket_instance, command.split(" ")[1])
            print(server_config)
        # Lets the user send messages to other users by typing @username message
        elif (command.startswith("@")):
            message_list = command.split()
            user_name = message_list[0][1:]
            message = ' '.join(message_list[1:])
            send_message = f"SEND {user_name} {message}\n"
            socket_instance.sendto(send_message.encode(),
                                   (HOST_NAME, PORT_NUMBER))
        else:
            # if command is invalid, it returns none and `server_output_to_msg() prints the error `
            print(server_output_to_msg(None))
    return


def server_output_to_msg(server_output):
    """
    This function translates server codes into user friendly 
    messages to be printed in the terminal.
    """
    if server_output is None:
        return "Error with given command or server response."
    if (type(server_output) != str):
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
    elif server_output == "IN-USE\n":
        return "User already exists. Please use a different one!"


def main():
    socket_instance = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    user = handshake(socket_instance)
    user = user[0]
    server_output = user.decode('ascii')
    while (not server_output.startswith("HELLO")):
        print(server_output_to_msg(user))
        socket_instance = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # if username is taken, user tries again
        user = handshake(socket_instance)
        user = user[0]
        server_output = user.decode('ascii')

    configure_server(socket_instance, set_drop=0.5)

    print(server_output_to_msg(user))
    print("Please always enter your command in the empty new line: ")
    stop_thread = threading.Event()
    input_thread = threading.Thread(
        target=handle_user_input, args=(socket_instance, stop_thread))
    socket_thread = threading.Thread(
        target=handle_socket, args=(socket_instance, stop_thread))

    input_thread.start()
    socket_thread.start()

    input_thread.join()
    socket_thread.join()

    socket_instance.close()
    sys.exit()  # Exit the program


main()
