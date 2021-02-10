#!/usr/bin/env python3

import event


def sip_recv(params):
    message, address = params
    event.put('recv_response', (message, ))


def sip_send(params):
    message, address = params
    event.put('send_packet', (message, address))


def init():
    event.regist('recv_packet', sip_recv)
    event.regist('send_request', sip_send)
