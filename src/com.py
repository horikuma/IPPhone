#!/usr/bin/env python3

import event
import lib
from sipframe import SipFrame


def sip_recv(event_id, params):
    message, address = params

    frame = SipFrame(message)
    event.put(f'recv_{frame.get("kind")}', (frame, ))


def sip_send(event_id, params):
    frame, address = params

    event.put('send_packet', (frame.to_message(), address))


def init():
    event.regist('recv_packet', sip_recv)
    event.regist('send_request', sip_send)
    event.regist('send_response', sip_send)
