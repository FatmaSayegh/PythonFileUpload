#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import socket
import helpers as helper
args = sys.argv;

commands = ["put", "get", "list"]

def exit_error(*msgs):
    for msg in msgs:
        print(msg)
    exit(1)
    
def manage_invalid_format():
    exit_error("Please use the following command:","python client.py <hostname> <port> <put filename|get filename|list>")
               
if len(args) < 4:
     manage_invalid_format()

# check arg length before getting command
command = args[3].lower()

if not command in commands:
    manage_invalid_format()

file_name = None

if command in commands[0:2]:
    if (len(args) != 5):
        manage_invalid_format()
    
    file_name = args[4]
    if command == "put" and not helper.file_helper.isfile(file_name):
        exit_error("Couldn't find the file " + file_name)

port = -1;
try:
    port = int(args[2]);
except:
    exit("Port must be an integer")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = (args[1], port) 

str_server_address = str(server_address[0]) + ":" + str(server_address[1])

try:
    server_socket.connect(server_address)
    print("Successfully conneted to",str_server_address)
except Exception as e:
    exit_error("Failed to connect, reason: " + str(e))
    



if command == "get":
    helper.send_msg(server_socket, "get " + file_name)
    helper.recv_file(server_socket, "downloads")
elif command == "put":
    response = helper.send_msg_with_response(server_socket, "put")
    # wait for response or data will be collated
    if "ok" in response:
        helper.send_file(server_socket, file_name, "")
elif command == "list":
    helper.send_msg(server_socket, "list")
    helper.recv_listing(server_socket)

server_socket.close()
