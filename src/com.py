#!/usr/bin/env python3

from rich.console import Console
from rich.panel import Panel

import event
import lib
import sipframe

response_reason = {
    200: 'OK',
}

message_template = {
    'request': '\r\n'.join([
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
        'Content-Length: 0',
        '',
        '',
    ]),
    'response': '\r\n'.join([
        'SIP/2.0 <response_code> <response_reason>',
        'Via: <via>',
        'Max-Forwards: 70',
        'From: <from>',
        'To: <sip:<local_username>@<local_domainname>><local_tag>',
        'Call-ID: <callid>',
        'CSeq: <remote_cseq_number> <method>',
        'User-Agent: horikuma IPPhone',
        'Contact: <sip:<local_username>@<local_domainname>:<local_port>>',
        'Allow: INVITE, ACK, BYE, CANCEL, UPDATE',
        'Content-Type: <content_type>',
        'Content-Length: <content_length>',
        '',
        '<body>',
    ])
}


headder_priority = [
    'Via',
    'Call-ID',
    'From',
    'To',
    'CSeq',
    'Contact',
    'Max-Forwards',
    'Expires',
    'Authorization',
    'Content-Length',
]

default_headers = {
    'Via',
    'Call-ID',
    'From',
    'To',
    'CSeq',
    'Max-Forwards',
}

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
    frame = sipframe.SipFrame(message).frame
    event.put(f'recv_{frame["kind"]}', (frame, ))
    display('R', frame)


def sip_send(event_id, params):
    frame, address = params

    template_message = lib.replace_all(message_template['request'], frame)
    template_frame = sipframe.SipFrame(template_message).frame
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


def sip_send_response(event_id, params):
    frame, address = params

    frame.update({
        'response_reason': response_reason[frame['response_code']],
    })

    message = lib.replace_all(message_template['response'], frame)
    message = message.replace('Content-Type: <content_type>\r\n', '')
    event.put('send_packet', (message, address))
    display('S', frame)


def init():
    event.regist('recv_packet', sip_recv)
    event.regist('send_request', sip_send)
    event.regist('send_response', sip_send_response)
