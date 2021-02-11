#!/usr/bin/env python3

import event
import lib


def sip_recv(params):
    message, address = params
    frame = lib.parse_message(message)
    event.put('recv_response', (frame, ))


def sip_send(params):
    frame, address, template = params
    message = lib.replace_all(template, frame)
    event.put('send_packet', (message, address))


def init():
    event.regist('recv_packet', sip_recv)
    event.regist('send_request', sip_send)
