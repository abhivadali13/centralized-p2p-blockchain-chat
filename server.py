#!/usr/bin/env python3
"""Server for multithreaded (asynchronous) chat application."""
from socket import AF_INET, socket, SOCK_STREAM
from easychain.blockchain import Message, Block, Blockchain
from threading import Thread
import string
import random
import _pickle as pickle
import sys


def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s has connected." % client_address)
        client.send(bytes("Welcome to the linked highway!\n", "utf8"))
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,client_address)).start()


def handle_client(client, client_address):  # Takes client socket as argument.
    """Handles a single client connection."""
    cars = random.choice(["Toyota", "Honda", "Tesla", "Nissan", "Ford", "Dodge"])
    license_plate = "".join(random.sample(string.ascii_letters.upper(),3)) + "-" + "".join(map(str, random.sample(range(10),3)))
    name = cars + " " + license_plate
    welcome = 'Car %s! If you ever want to quit, type {quit} to exit.' % name
    format_msg = 'This is the format of the messages: [STATE, LOCATION, SPEED, UUID, TIME, BRAKE]'
    
    client.send(bytes(welcome + "\n", "utf8"))
    client.send(bytes(format_msg + "\n", "utf8"))
    msg = "%s has joined the highway!" % name
    broadcast(bytes(msg, "utf8"))
    clients[client] = name

    while True:
        msg = client.recv(BUFSIZ)
        if msg != bytes("{quit}", "utf8"):
            print("SERVER RECEIVED: " + msg.decode("utf8"))
            B1 = Block()
            B1.add_message(Message(msg.decode("utf8")))
            B1.seal()
            print("SERVER CREATED BLOCK for " + msg.decode("utf8"))

            chain.add_block(B1)
            print("ADDED TO BLOCKCHAIN for " + msg.decode("utf8"))

            msg_chain = {name+": "+msg.decode("utf8"): chain}
            data = pickle.dumps(msg_chain, -1)

            broadcast(data)
        else:
            print("IN QUITTING CLIENT")
            client.close()
            del clients[client]
            broadcast(bytes("%s has left the highway." % name, "utf8"))
            break


def broadcast(msg, prefix=""):  # prefix is for name identification.
    """Broadcasts a message to all the clients."""

    for sock in clients:
        print(msg)
        print("Sent message to " + str(sock))
        sock.send(bytes(prefix, "utf8")+msg)

chain = Blockchain()        
clients = {}
addresses = {}

HOST = ''
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.bind(ADDR)

if __name__ == "__main__":
    try:
        SERVER.listen(5)
        print("Waiting for connection...")
        ACCEPT_THREAD = Thread(target=accept_incoming_connections)
        ACCEPT_THREAD.daemon = True
        ACCEPT_THREAD.start()
        ACCEPT_THREAD.join()
        SERVER.close()
    except KeyboardInterrupt:
        sys.exit(0)