#!/usr/bin/env python3

import event
import socket


sock = None


def recv():
    while True:
        message, address = sock.recvfrom(1024)
        message = message.decode()
        event.put('recv_packet', (message, address))
        # print(message)


def send(event_id, params):
    message, address = params
    sock.sendto(message.encode(), address)
    # print(message)


def init(local_address):
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(local_address)

    event.regist('send_packet', send)
