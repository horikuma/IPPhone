#!/usr/bin/env python3

from rich.console import Console
from rich.panel import Panel

import event
import lib

request_message_template = '\r\n'.join([
    '<method> sip:<remote_domainname>:<remote_port> SIP/2.0',
    'Via: SIP/2.0/UDP <local_domainname>:<local_port><branch>',
    'Max-Forwards: 70',
    'From: <sip:<local_username>@<local_domainname>><local_tag>',
    'To: <sip:<remote_username>@<remote_domainname>><remote_tag>',
    'Call-ID: <callid>',
    'CSeq: <local_cseq_number> <method>',
    'User-Agent: horikuma IPPhone',
    'Contact: <sip:<local_username>@<local_domainname>:<local_port>>',
    'Expires: <expires>',
    'Allow: INVITE, ACK, BYE, CANCEL, UPDATE',
    'Authorization: <authorization>',
    'Content-Length:  0',
    '',
    '',
])


headder_priority = [
    'To',
    'From',
    'CSeq',
    'Call-ID',
    'Max-Forwards',
    'Via',
    'Authorization',
    'Expires',
    'Contact',
]

default_headers = {
    'To',
    'From',
    'CSeq',
    'Call-ID',
    'Max-Forwards',
    'Via',
}

con = Console()


def display(dir, frame):
    method = frame['method']
    cseq_num = frame.get('remote_cseq_number')
    if not cseq_num:
        cseq_num = frame.get('local_cseq_number')

    if 'request' == frame['kind']:
        con.print(Panel(f'[{dir}] {method}-{cseq_num}'))
    else:
        rcode = frame['response_code']
        con.print(Panel(f'[{dir}] {method}-{cseq_num} ({rcode})'))


def sip_recv(event_id, params):
    message, address = params
    frame = lib.parse_message(message)
    event.put(f'recv_{frame["kind"]}', (frame, ))
    display('R', frame)


def sip_send(event_id, params):
    frame, address = params

    template_message = lib.replace_all(request_message_template, frame)
    template_frame = lib.parse_message(template_message)
    header = ''
    headers = default_headers.copy()
    if 'add_header' in frame:
        headers |= frame['add_header']
    if 'remove_header' in frame:
        headers -= frame['remove_header']
    for h in headder_priority:
        if not h in headers:
            continue
        if not h in template_frame['header']:
            continue
        if not template_frame['header'][h]:
            continue
        header += f'{h}: {template_frame["header"][h]}\r\n'

    message = '\r\n'.join([
        template_frame['start-line'],
        header,
        template_frame['body'],
    ])

    event.put('send_packet', (message, address))
    display('S', frame)


def init():
    event.regist('recv_packet', sip_recv)
    event.regist('send_request', sip_send)
