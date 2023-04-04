import socket


HOST_NAME = "143.47.184.219"
PORT_NUMBER = 5378


def handshake(s):
    # Connect to another application.
    s.connect((HOST_NAME, PORT_NUMBER))
    
    # Asking for a unique username
    user_name = input("Please enter a user name: ")
    user_name = f"HELLO-FROM {user_name}\n"
    name_bytes_sent = s.send(user_name.encode())
    buffer = s.recv(2048)
    return buffer

def userCommand(s):
    command = input("Please enter a command: ")

    if(command == "!quit"): # Lets the user shutdown the client by typing !quit
        return None
    elif(command == "!who"): #Lets the user list all currently logged-in users by typing !who
        user_list = "LIST\n"
        list_bytes_sent = s.send(user_list.encode())
    elif(command.startswith("@")): # Lets the user send messages to other users by typing @username message
        message_list = command.split()
        user_name = message_list[0][1:]
        message = message_list[1]
        send_message = f"SEND {user_name} {message}\n"
        list_bytes_sent = s.send(send_message.encode())
    buffer = s.recv(2048)
    return buffer



# Errors still need to be handled
def main():
    # Create a new socket.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    user_name = handshake(s) # Response from server is returned
    while(user_name == b'IN-USE\n'): # This asks for another name if the chosen name is already taken.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        user_name = handshake(s)
    print(user_name)
    
    # We let the user interact with the server
    command = userCommand(s) # Response from server is returned and none is user quits
    while(command != None):
        print(command)
        command = userCommand(s)

    # This still needs to be worked on, but we should be able to messages from other users and display them to the user
    # I'm thinking, we need to use threading 
    # received_message = s.recv(2048)
    # print(received_message)

    # Close connection.
    s.close()

main()