#!/usr/bin/env python3
"""Script for Tkinter GUI chat client."""
from socket import AF_INET, socket, SOCK_STREAM
from easychain.blockchain import Message, Block, Blockchain, InvalidBlockchain
from threading import Thread
from time import time, sleep
from random import randint,choice
from uuid import uuid4
import tkinter
import _pickle as pickle 
import numpy as np
import sys


def receive():
    """Handles receiving of messages."""

    while True:
        # print(time())
        global state
        global chain
        global brakeLoc
        global brakeTime
        global brakingOn
        global name

        print("RECEIVE: " + state)

        try:
            rcvd = client_socket.recv(BUFSIZ)
            print("RECEIVED:" + str(type(rcvd)))
        except OSError:  # Possibly client has left the chat.
            # print("IN OS ERROR")
            break

        try:
            if state != "BRAKE":
                state = "CONNECTED"
            # print("IN GENERAL CASE")
            # print(rcvd)
            msg = rcvd.decode("utf8")
            if msg.startswith("Car"):
                name = msg.split(" ")[1] + " " + msg.split(" ")[2].strip("!")
                print(name)
            msg_list.insert(tkinter.END, msg)
        except UnicodeDecodeError as e:
            # print("IN PICKLE CASE")
            # print(rcvd)
            try:
                msg = pickle.loads(rcvd)
                # print("GOT MESSAGE IN PICKLE CASE")
                chain = list(msg.values())[0]
                chain.validate()
                car_name = list(msg.keys())[0].split(":")[0].strip()
                print("CAR NAME:" + car_name)
                print("DATA:" + chain.blocks[-1].messages[0].data)
                status_data = chain.blocks[-1].messages[0].data.split(";")
                print("STATUS_DATA:",status_data)

                if status_data[0] == "BRAKE":
                    brakeLoc[car_name] = status_data[1].strip("(").strip(")").split(",")
                    brakeTime[car_name] = status_data[5]
                    print("BRAKE TIME:",brakeTime)
                    print("BRAKE LOC:", brakeLoc)
                elif status_data[0] == "RESTART":
                    print("IN RESTART")
                    if brakingOn == car_name:
                        state = "CONNECTED"
                        restartTime[name] = status_data[5]
                    restartTime[car_name] = status_data[5]
                    print("RESTART TIME:", restartTime)

                if (list(msg.keys())[0].split(":")[1].strip() == chain.blocks[-1].messages[0].data):
                    msg_list.insert(tkinter.END, list(msg.keys())[0])
            except EOFError:
                continue
        except InvalidBlockchain as e:
            print("Blockchain is invalid")
            break
        except socket.error:
            break


def read_the_socket():
    global location
    global state
    global brake
    global brakingOn
    print("TK STATE:" + state)
    print("BRAKE: " + str(brake))
    if state == "CONNECTED":
        # print(location)
        print("INSIDE:" + state)
        location_tup = "(" + ",".join(map(str,location)) + ")"

        directions = ["N"]
        # directions = ["N", "W", "S", "E"]
        chosen = choice(directions)
        future = location
        print("CHOSEN:" + chosen)
        if chosen == "N":
            print("IN NORTH")
            future = (location[0], location[1] + speed)
        elif chosen == "W":
            print("IN WEST")
            future = (location[0] - speed, location[1])
        elif chosen == "S":
            print("IN SOUTH")
            future = (location[0], location[1] - speed)
        else:
            print("IN EAST")
            future = (location[0] + speed, location[1])

        for brakeVal in brakeLoc.items():
            print("IN FOR LOOP: ",brakeVal)
            print("DIFF:", np.abs(sum(np.subtract(future, tuple(map(int,brakeVal[1]))))))
            if np.abs(sum(np.subtract(future, tuple(map(int,brakeVal[1]))))) <= 3:
                print(brakeVal[0] in brakeTime.keys() and brakeVal[0] not in restartTime.keys())
                if (brakeVal[0] in brakeTime.keys() and brakeVal[0] not in restartTime.keys()) or (brakeTime[brakeVal[0]] >= restartTime[brakeVal[0]]):
                    state = "BRAKE"
                    brake = True
                    brakingOn = brakeVal[0]
                    status = ";".join([state, location_tup, str(speed), str(int(uuid4())), str(brake), str(int(time()))])
                    my_msg.set(status)
                    send()
        
        if state != "BRAKE": 
            print("IN IF STATEMENT:")
            status = ";".join([state, location_tup, str(speed), str(int(uuid4())), str(brake), str(int(time()))])
            my_msg.set(status)
            send()
            location = future
            print("FUTURE LOCATION: ", location)



    top.after(20000, read_the_socket)

def send(event=None):  # event is passed by binders.
    """Handles sending of messages."""
    global state
    msg = my_msg.get()
    my_msg.set("OPTIONS: Brake")
    if msg.upper() == "BRAKE" and state == "CONNECTED":
        global brake
        state = "BRAKE"
        print("SEND:" + state)
        brake = True
        location_tup = "(" + ",".join(map(str,location)) + ")"
        status = ";".join([state, location_tup, str(speed), str(int(uuid4())), str(brake), str(int(time()))])
        client_socket.send(bytes(status, "utf8"))
        my_msg.set("OPTIONS: Restart")
    elif msg.upper() == "RESTART" and state == "BRAKE":
        state = "RESTART"
        print("SEND:" + state)
        brake = False
        location_tup = "(" + ",".join(map(str,location)) + ")"
        status = ";".join([state, location_tup, str(speed), str(int(uuid4())), str(brake), str(int(time()))])
        client_socket.send(bytes(status, "utf8"))
        my_msg.set("OPTIONS: Brake")
    elif msg == "{quit}":
        print("IN QUIT")
        print(msg)
        client_socket.send(bytes(msg,"utf8"))
        client_socket.close()
        top.quit()
    else:
        client_socket.send(bytes(msg,"utf8"))


def on_closing(event=None):
    print("IN ON_CLOSING")
    """This function is to be called when the window is closed."""
    my_msg.set("{quit}")
    send()

state = "NOT CONNECTED"
location = (0, 0)
# location = (randint(0,10), randint(0,10))
speed = randint(1,5)
brake = False

brakingOn = ""
name = ""

brakeLoc = {}
brakeTime = {}
restartTime = {}

top = tkinter.Tk()
top.title("Traffic")

messages_frame = tkinter.Frame(top)
my_msg = tkinter.StringVar()  # For the messages to be sent.
my_msg.set("")
scrollbar = tkinter.Scrollbar(messages_frame)  # To navigate through past messages.
# Following will contain the messages.
msg_list = tkinter.Listbox(messages_frame, height=20, width=130, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()
messages_frame.pack()

entry_field = tkinter.Entry(top, textvariable=my_msg)
entry_field.bind("<Return>", send)
entry_field.pack()
send_button = tkinter.Button(top, text="Send", command=send)
send_button.pack()

top.after_idle(read_the_socket)
top.protocol("WM_DELETE_WINDOW", on_closing)


#----Now comes the sockets part----
# HOST = input('Enter host: ')
# PORT = input('Enter port: ')
# if not PORT:
#     PORT = 33000
# else:
#     PORT = int(PORT)

BUFSIZ = 1024*5
ADDR = ("localhost", 33000)

chain = Blockchain()

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDR)

receive_thread = Thread(target=receive)
receive_thread.start()
tkinter.mainloop()  # Starts GUI execution.
