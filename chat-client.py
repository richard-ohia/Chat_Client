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


HOST_NAME = "143.47.184.219"
PORT_NUMBER = 5378

"""
This function takes a socket object s as an argument and performs a handshake with the server. 
It connects to the server using the HOST_NAME and PORT_NUMBER constants, 
asks the user for a unique username, sends it to the server and receives a response from the server. 

:param s: socket object
:returns buffer: the response from the server
"""
def handshake(s):
    # Connect to another application.
    s.connect((HOST_NAME, PORT_NUMBER))
    
    # Asking for a unique username
    user_name = input("Please enter a user name: ")
    user_name = f"HELLO-FROM {user_name}\n"
    name_bytes_sent = s.send(user_name.encode())
    buffer = s.recv(2048)
    return buffer


"""
This function takes a socket object s as an argument and allows the user to interact with the server by entering commands. 
The user can enter !quit to shutdown the client, 
!who to list all currently logged-in users or @username message to send a message to another user. 
The function sends the appropriate command to the server and receives a response from the server. 

:param s: socket object
:returns buffer: the response from the server
"""
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
        message = ' '.join(message_list[1:])
        send_message = f"SEND {user_name} {message}\n"
        list_bytes_sent = s.send(send_message.encode())
    buffer = s.recv(2048)
    return buffer


"""
This function creates a new socket object, performs a handshake with the server using the handshake(s) function 
and allows the user to interact with the server using the userCommand(s) function. 
If the chosen username is already taken, it asks for another name until a unique username is entered. 
The function prints responses from the server and closes the socket when finished.
"""
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
    # I think we need to use threading 
    # received_message = s.recv(2048)
    # print(received_message)
    

    # Close connection.
    s.close()

main()