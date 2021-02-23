#!/usr/bin/env python3

import event
import lib

request_message_template = '\r\n'.join([
    '<method> sip:asterisk@<server_address>:5060 SIP/2.0',
    'Via: SIP/2.0/UDP <server_address>:5061;rport;branch=z9hG4bK<branch>',
    'Max-Forwards: 70',
    'From: <sip:<local_username>@<local_domainname>><local_tag>',
    'To: <sip:<remote_username>@<remote_domainname>><remote_tag>',
    'Call-ID: <callid>',
    'CSeq: <local_cseq_number> <method>',
    'User-Agent: PJSUA v2.10-dev Linux-5.4.72/x86_64/glibc-2.31',
    'Contact: <sip:6002@<server_address>:5061;ob>',
    'Expires: <expires>',
    'Allow: PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS',
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


def sip_recv(event_id, params):
    message, address = params
    frame = lib.parse_message(message)
    event.put('recv_response', (frame, ))


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


def init():
    event.regist('recv_packet', sip_recv)
    event.regist('send_request', sip_send)
