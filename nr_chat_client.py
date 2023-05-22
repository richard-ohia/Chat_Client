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
import random
import threading
import sys
import time

HOST_NAME = "143.47.184.219"
PORT_NUMBER = 5382
BUFFER_SIZE = 1024

SEQUENCE_NUMBER = random.randint(16, 2**32)
ACKNOWLEDGEMENT_NUMBER = 0

MESSAGE = ""

MESSAGE_QUEUE = []

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


def extract_sequence_number(message):
    sequence = message.split("**90")[0]
    return sequence

def extract_acknowledgment_number(message):
    acknowledgment = message.split("**90")[1]
    return acknowledgment


def construct_message(sequence_number, acknowledgment, data):
    delimiter = "**90"
    return str(sequence_number) + delimiter + str(acknowledgment) + delimiter + data

def acknowledgement_check(msg):
    correct_ack = False
    global SEQUENCE_NUMBER
    start_time = time.time()
    received_ack_number = extract_acknowledgment_number(msg)
    while not correct_ack:
        if int(SEQUENCE_NUMBER) == int(received_ack_number):  # Correct ACK received
            SEQUENCE_NUMBER += 1
            correct_ack = True
            if(len(MESSAGE_QUEUE) != 0):
                MESSAGE_QUEUE.pop(0)
            print("Message was acknowledged.")
            break
        elif time.time() - start_time > 10:  # Timeout limit exceeded
            print("Timeout limit exceeded, resending message...")
            break
    return


def calculate_checksum(data):
    checksum = 0
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            # Get two bytes from the data
            word = (data[i] << 8) + data[i + 1]
            checksum += word

    # Add the carry if it exists
    if len(data) % 2 != 0:
        checksum += data[-1]

    # Fold the carry bits
    while checksum >> 16:
        checksum = (checksum & 0xFFFF) + (checksum >> 16)

    # Invert the bits to get the checksum
    checksum = ~checksum & 0xFFFF
    
    return data.decode() + "!check" + str(checksum)

def validate_checksum(data):
    # Extract the received checksum from the packet
    received_checksum = data.split("!check")[1]

    # Calculate the checksum of the data
    calculated_checksum = calculate_checksum((data.split("!check")[0]).encode())
    calculated_checksum = calculated_checksum.split("!check")[1]

    # Compare the received and calculated checksums
    if received_checksum == calculated_checksum:
        return True
    else:
        return False



def handle_socket(socket_instance, stop_thread):
    """
    This function takes a socket object socket_instance as an argument and listens for any message from the server. 
    We use a timer to restart the loop to check our stop_thread flag 
    """
    global SEQUENCE_NUMBER
    global ACKNOWLEDGEMENT_NUMBER
    socket_instance.settimeout(1.0)  # set the timeout to 1 second
    while not stop_thread.is_set():
        final_msg = ""
        msg = None
        isEnd = False
        try:
            while not isEnd:
                msg, addr= socket_instance.recvfrom(BUFFER_SIZE)
                final_msg += msg.decode('utf-8')
                if(final_msg[-1] == "\n"):
                    isEnd = True
        except socket.timeout:
            if(len(MESSAGE_QUEUE) > 0):
                message = MESSAGE_QUEUE[0]
                socket_instance.sendto(message.encode(),
                (HOST_NAME, PORT_NUMBER))
            continue  # timeout occurred, go back to the beginning of the loop
        except:
            print("Error in message detected!")
            continue
        if final_msg.startswith("DELIVERY"):
            msg_list = final_msg.split()

            sender = msg_list[1]
            decoded = ' '.join(msg_list[2:])
            # Extract sequence number from the received message
            received_sequence_number = extract_sequence_number(decoded)
            if(decoded.split("**90")[2] == ""):
                acknowledgement_check(decoded)
            else:
                if(not validate_checksum(decoded)):
                    print("Error in message detected!")
                    exit()
                if ACKNOWLEDGEMENT_NUMBER == 0 or int(received_sequence_number) == int(ACKNOWLEDGEMENT_NUMBER) or int(received_sequence_number) == int(ACKNOWLEDGEMENT_NUMBER) - 1:
                    ACKNOWLEDGEMENT_NUMBER = int(received_sequence_number)
    
                    # Construct the acknowledgment message
                    acknowledgment_message = construct_message(SEQUENCE_NUMBER, ACKNOWLEDGEMENT_NUMBER, "")

                    send_message = f"SEND {sender} {acknowledgment_message}\n"
                    # Send the acknowledgment message
                    socket_instance.sendto(send_message.encode(), (HOST_NAME, PORT_NUMBER))

                    # Increment the expected sequence number
                    ACKNOWLEDGEMENT_NUMBER += 1

                sent_message = decoded.split("**90")[2]
                sent_message =sent_message.split("!check")[0]
                print("\n" + msg_list[1] + " --> " + sent_message)
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
            # Construct the message with sequence number and acknowledgment
            constructed_message = construct_message(SEQUENCE_NUMBER, ACKNOWLEDGEMENT_NUMBER, message)
            constructed_message = calculate_checksum(constructed_message.encode())
            send_message = f"SEND {user_name} {constructed_message}\n"

            MESSAGE_QUEUE.append((send_message))

            if(len(MESSAGE_QUEUE) == 1):
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
        return "Server has sent your message or acknowledgment!\n"
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

    configure_server(socket_instance, set_flip=0)

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