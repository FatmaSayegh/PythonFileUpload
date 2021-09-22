#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path as file_helper
import os as folder_helper
# time was added for timeouts 
import time



# length of data to be sent and received at a time
SEND_RECV_LENGTH = 1024
# 1 GB max transfer
# 10^9 is 1GB in bytes
MAX_FILE_SIZE = 10**9 
# max length of file name
MAX_FILE_NAME_LENGTH = 64

# Timed out string
TIMED_OUT = "Timed Out"



# function to get the current time in milliseconds
# used for timeouts
millis = lambda: int(time.time()*1000)



# attempt to read a string message from the socket for a certain time
def read_msg(socket, timeout=1000):
    # get the current time
    start_time = millis()
    msg = ""
    
    # create a byte array with length 1
    # this is since if socket.recv was put here
    # its gonna wait until some data is recieved then do the while loop
    data = bytearray(1)
    # so long as the message does not end with a new line
    # and so long as 'millis() - start_time' which is the time since the function started 
    # is less than the timeout time, keep trying to recieve data
    while (len(data) > 0) and (not "\n" in msg) and (millis()-start_time < timeout):
        try:
            data = socket.recv(SEND_RECV_LENGTH)
            msg += data.decode()           
        except Exception as e:
            msg = "FAILED to send message"
        
    msg = msg.replace("\n","")
    return TIMED_OUT if msg == "" else msg;

# send string message to a socket
def send_msg(socket, msg, end="\n"):
    # adding \n at the end to know when to terminate
    if not end in msg:
        msg += end
    try:
        socket.sendall(str.encode(msg))
        return True
    except:
        return False
    
# prints error to console and sends it to socket
def send_error(socket, error, label=""):
    error = label + "Error: " + error
    print(error)
    return send_msg(socket, error)
        

# sends message and waits for read message
def send_msg_with_response(socket, msg, timeout=1000):
    if not send_msg(socket, msg):
        return "ERROR: Failed to send message"
    return read_msg(socket, timeout)
    
    
        
# function to send file from client or server
# locates the file 
# asks the socket if the file exists
# sends it to the socket if it doesnt
def send_file(socket, file_name, _dir="uploads"):
    # create the directory cuz maybe it doesn't exist
    if len(_dir.strip()) != 0:
        folder_helper.makedirs(_dir, exist_ok=True)
        _dir += "/"
    
    # the directory is different for the server and the client
    # thats why it is an argument
    file_dir = _dir + file_name
    
    # check if this file exists
    if not file_helper.isfile(file_dir):
        send_error(socket, "Couldn't find the file " + file_name)
        return
    
    # get the file size
    size = file_helper.getsize(file_dir)
    
    
    if (size <=0):
        send_error(socket, "File must be more than 0")
        return
        
    if (size > MAX_FILE_SIZE):
        send_error(socket, "File size is too big")
        return
    
    if (len(file_name) > MAX_FILE_NAME_LENGTH):
        send_error(socket, "File name is too long")
        return
    
    # sent to the server and wait for a response
    # here the timeout is 1000, which can be seen in read_msg function
    response = send_msg_with_response(socket, "file_info " + str(file_name) + " " + str(size))
    # if no ok was recieved to start sending the file, probably some error occured and was sent here using send_error
    # so we pring the error
    
    if not "ok" in response:
        print(response)
        return
    
    # progress is 0 since file sending didn't start
    progress = 0
    
    # open the file in read binary mode so that any file type could be sent
    # simply by sending the binary data, and receiving this data, the file is copied :)
    file_reader = open(file_dir, 'rb')
    
    # just for the user output
    print("Started sending the file", file_name, "of size",size,"bytes")
    
    # start reading from the file
    data = file_reader.read(SEND_RECV_LENGTH)
    # so long as there is data available that was read from the file
    while len(data) > 0:
        # try to do some stuff
        try:
            # send the data to the socket
            socket.sendall(data)
            # increment progress by the length of this data
            progress += len(data)
            # print the progress
            print_progress(progress, size)
            # re-read the data
            data = file_reader.read(SEND_RECV_LENGTH)
        except Exception as e:
            print()
            print("Failed to send due to an error", e)
            break
        

    # print nothing because the progress printing was printing stuff on the same line
    print()
    
    # never forget to close the file
    file_reader.close()
    
    # if an exception occured in the while loop on top
    # progress will never reach 100
    # so the sending will fail
    # From the client side, if the progress isn't 100, it should delete the file
    if get_progress(progress, size) < 100:
        print("File sending was incomplete...")
    else:
        print("File sent successfully!")
    
        

        
# function to recieve a file from a socket to a certain directory
# the function attempts to read the file information from the socket
# then downloads the file
# this makes it so 
def recv_file(socket, _dir="uploads"):
    # create the directory cuz maybe it doesn't exist
    if len(_dir.strip()) != 0:
        folder_helper.makedirs(_dir, exist_ok=True)
    
    # wait to read file info from the socket
    # this makes it so the function doesn't have to specify the file name and file size
    # useful for future purposes the user requests something and doesn't know the file name
    # example: downloading a random file, request to server a random file, the server checks its files, choses a random file, then sends the client the file information, then sends the data.. 
    msg_info = read_msg(socket)
    
    # if the msg is not a file info message, then no file is to be recieved 
    if not "file_info" in msg_info:
        print(msg_info)
        return
    
    # format: file_info fileName fileSize
    # so we split the recieved message by a ' ' <- space
    msg_info = msg_info.split()
    
    # load them from the split message
    file_name, file_size = msg_info[1], int(msg_info[2])
    
    if file_size <=0:
        send_error(socket, "File must be more than 0")
        return
        
    #  file path variable based on directory
    file_path = _dir + "/" + file_name
    
    
    # checks if the file exists or not
    if file_helper.isfile(file_path):
        # if exists, return to terminate the function and send an error
        # reciever is the side recieving the file
        send_error(socket, "The file already exists...", label="Receiving ")
        return
    
    # if it doesn't exist
    # tell the sender ok, send the file
    if not send_msg(socket, "ok"):
        print("Failed to send OK")
        return;
    
    # progress 0
    progress = 0
    
    # open the file in writing binary mode
    file_writer = open(file_path, "wb")
    
    # log
    print("Recieving File data...")
    
    try:
        # recieve data from the socket based on the send recieve length
        data = socket.recv(SEND_RECV_LENGTH)
        # run this loop so long as the data exists
        while len(data) > 0:
            file_writer.write(data)
            progress += len(data)
            print_progress(progress, file_size)
            data = socket.recv(SEND_RECV_LENGTH)
    except Exception as e:
            print()
            print("Failed to receive file due to an error", e)

        
    # print nothing because the progress printing was printing stuff on the same line
    print()
    # close the file
    file_writer.close()
    
    # check if the file was fully received
    if get_progress(progress, file_size) < 100:
        print("File receive was incomplete")
        folder_helper.remove(file_path)
    else:
        print("File successfully received")
   
        

# send listing function. 
# this function checks if the folder exists, and lists its directories and files
# it calls this function again on these files and directories so that if it were a folder
# it lists the sub-directories by recursion
def send_listing(socket, _dir="uploads", tabs=""):
    if not file_helper.isdir(_dir):
        # if its the first call of the function, tabs is empty
        # next time the function is called by recursion in the loop
        # a tab is added to print the sub directories
        if tabs == "":
            send_error(socket, "Couldn't find any files.")
        return
    
    print("Sending directory listing...")
    
    for directory in folder_helper.listdir(_dir):
        """
        send the message which consists of the the tabs and the directory
        eg:  ----folderName
        eg:      ----somefile.txt
        """
        # this was made before i read i dont have to do sub directories
        if not send_msg(socket, tabs+"---"+directory):
            print("Failed to send", str(director))
        
        
        
        """
        call the function again to check if the directory is a folder and not a file
        so that we can print the sub folders
        add a tab so the sub folders are tabbed to appear in a nice way as shown abpove
        """
        # comment this line to remove sub directories
        send_listing(socket, _dir + "/" + directory, tabs+"\t")
                
        
    print("Done!")
    

# simply receiving listing is receiving messages
# the client.py requests from the server a listing
# then this function is called for the client, and the above one is called for the server
# there is a timeout in read_msg which is around one second
def recv_listing(socket):
    _str = "Here is a list of files on the server"
    while _str != TIMED_OUT:
        print(_str)
        _str = read_msg(socket)
        

# calculates percentage progress based on two numbers
def get_progress(progress, goal):
    return 100 -  (goal-progress)*100/goal

#print progress on the same line
def print_progress(progress, goal):
    print('\r' + "Progress: ", int(get_progress(progress, goal)), end="")
