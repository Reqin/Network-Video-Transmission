# coding:utf8

import socket
import time


class Communicator:
    def __init__(self, address, conn=None):
        self.message_send = None
        self.message_recv = None
        self.sock = conn
        if not conn:
            print(55)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.__connect(address)

    def __connect(self, address):
        while True:
            try:
                self.sock.connect(address)
                break
            except socket.error as error:
                print(error)
                time.sleep(1)

    def set_message(self, message):
        self.message_send = message
        return self

    def send(self):
        self.sock.send(self.message_send)

    def recv(self, length):
        return self.sock.recv(length, socket.MSG_WAITALL)

    def encode(self, length):
        self.message_send = str.encode(str(self.message_send).ljust(length))
        return self
