#!/usr/bin/env python3

from rich.console import Console
from rich.panel import Panel

import event
import lib
from sipframe import SipFrame

con = Console()


def display(dir, frame):
    method = frame['method']
    cseq_num = frame.get('remote_cseq_number')  # TODO
    if not cseq_num:
        cseq_num = frame.get('local_cseq_number')

    if 'request' == frame['kind']:
        con.print(Panel(f'[{dir}] {method}-{cseq_num}'))
    else:
        rcode = frame['response_code']
        con.print(Panel(f'[{dir}] {method}-{cseq_num} ({rcode})'))


def sip_recv(event_id, params):
    message, address = params
    frame = SipFrame('recv', message).frame
    event.put(f'recv_{frame["kind"]}', (frame, ))
    display('R', frame)


def sip_send(event_id, params):
    frame, address = params

    frame = SipFrame('send', frame)
    event.put('send_packet', (frame.to_message(frame), address))
    display('S', frame.frame)


def init():
    event.regist('recv_packet', sip_recv)
    event.regist('send_request', sip_send)
    event.regist('send_response', sip_send)
