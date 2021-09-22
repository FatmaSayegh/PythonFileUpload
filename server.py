#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import socket
# helpers has some functions
import helpers as helper


should_debug = False

def debug(*args, end="\n"):
    if should_debug:
        print(*args, end)


        

# this function manages client commands
# this function reads the client command
# analyzes it 
def manage_client(socket):
    debug("Waiting for client command.")
    
    # waits a certain time for the client command
    # since the command is instantly sent when the client connects
    # we can directly get the command without waiting too long
    client_command = helper.read_msg(socket)
    

    print("Command from Client:", client_command)
    
    
    # if the client wants a file, client sends "get fileName"
    # here server is analyzing this
    if "get" in client_command:
        # get the file name
        file_name = client_command.split()[1]
        # check if not exist
        if not helper.file_helper.isfile("uploads/" + file_name):
            helper.send_error(socket, "Couldn't find the file " + file_name)
        # if exists
        else:
             helper.send_file(socket, file_name)
        
    # if the clients want to put a file, we send the put command from the client
    # server sends ok, when client recieves ok, client sends file
    # this is when server recvs file
    elif "put" in client_command:
        # send ok to client
        helper.send_msg(socket, "ok")
        
        # receive file
        helper.recv_file(socket) # there is a 1000 second timeout in this since it is found in read_msg function
    # clients sends a command list
    elif "list" in client_command:
        # server responds with the listing
        helper.send_listing(socket)

#get system arguments

# get the command arguments


# python server.py port

# gets the arguments of the command
args = sys.argv;

# command: python server.py port ---> 2 args
# this is done so that if the argument has more or less inputs than required
# it may cause errors in the future
# so we make sure it only has 2 arguments
if len(args) != 2:
    print("Please Specify the port number")
    exit(1);

# we need to make sure that the input port is an integer
# in python sockets, the port must be a number greater than 0

port = -1 # assume port is negative, since port must be positive

# i want to get the port from the user input
# i dont care about my assumption
try:
    # try to make the port that the user input an integer
    # args[1] is the input port
    port = int(args[1]);
except:
    # exit if failed
    print("Port must be an integer")
    exit(1)

    
# since we exit if it faied, port should be always an integer here
# we need to make sure port is positive
if port < 0:
    print("Chose a positive port value")
    exit(1)
    
# Create socket, (host, port), tcp
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#bind socket
try:
    server_socket.bind(("0.0.0.0", port))  # this binding may cause an error due to invalid ip or port, or because another server is connected
    print("Server socket connected to 0.0.0.0:" + str(port))
except Exception as e:
    print("Server failed to bind, reason:", e)
    exit(1)
    
# self explanatory
print("Server socket is listening and will queue up to 5 clients")
server_socket.listen(5) # queues up to 5 clients

# so long as the program is running
try:
    while True:
        print()
        print("Waiting for client...")
        # socket.accept() waits for a client and gives the socket and address
        client_socket, client_address = server_socket.accept() # this function pauses the code until a client comes
        client_socket.settimeout(1)

        # print nice stuff
        print("New Client connected, client address:", str(client_address));  

        # manage the client in the function above
        manage_client(client_socket)


        # close the socket
        client_socket.close()
        print("Client disconnected")
except Exception as e:
    print("Error", e)
finally:
    print("")
    # close server socket when the loop on top finishes
    server_socket.shutdown()
    server_socket.close()


