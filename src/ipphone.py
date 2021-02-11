#!/usr/bin/env python3

import re
import sys
import threading

import com
import drv
import event
import lib

first_send_message_template = '''\
REGISTER sip:asterisk@<server_address>:5060 SIP/2.0
Via: SIP/2.0/UDP <server_address>:5061;rport;branch=z9hG4bKPjEMKNT1arBd1xzjzfSCDYJAqS-1U1vqOl
Max-Forwards: 70
From: <sip:6002@<server_address>>;tag=0E5AsBqTALBI8zv1roq682BWtJt6wJOu
To: <sip:6002@<server_address>>
Call-ID: deUH4-p2IpimBfdJvwFAHH8EVJRay1BU
CSeq: <cseq_number> REGISTER
User-Agent: PJSUA v2.10-dev Linux-5.4.72/x86_64/glibc-2.31
Contact: <sip:6002@<server_address>:5061;ob>
Expires: 300
Allow: PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS
Content-Length:  0
'''

second_send_message_template = '''\
REGISTER sip:asterisk@<server_address>:5060 SIP/2.0
Via: SIP/2.0/UDP <server_address>:5061;rport;branch=z9hG4bKPjEMKNT1arBd1xzjzfSCDYJAqS-1U1vqOl
Max-Forwards: 70
From: <sip:6002@<server_address>>;tag=0E5AsBqTALBI8zv1roq682BWtJt6wJOu
To: <sip:6002@<server_address>>
Call-ID: deUH4-p2IpimBfdJvwFAHH8EVJRay1BU
CSeq: <cseq_number> REGISTER
User-Agent: PJSUA v2.10-dev Linux-5.4.72/x86_64/glibc-2.31
Contact: <sip:6002@<server_address>:5061;ob>
Expires: 300
Allow: PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS
Authorization: <authorization>
Content-Length:  0
'''

server_address = None
remote_address = None


def cmd():
    c = input()
    if '+a' == c:
        event.put('regist')
    if 'exit' == c:
        exit()


def register_regist(params):
    send_frame = {
        'server_address': server_address,
        'cseq_number': 1,
    }
    event.put('send_request', (
        send_frame,
        remote_address,
        first_send_message_template
    ))


def register_recv_response(params):
    if not hasattr(register_recv_response, 'count'):
        register_recv_response.count = 1

    if 1 < register_recv_response.count:
        return
    register_recv_response.count += 1

    recv_frame = params[0]
    authorization_config = lib.parse_header(
        recv_frame['header']['WWW-Authenticate']
    )
    authorization_config.update({
        'method': 'REGISTER',
        'username': '6002',
        'password': 'unsecurepassword',
        'uri': f'sip:asterisk@{server_address}:5060',
    })
    authorization = lib.build_authorization(authorization_config)
    send_frame = {
        'server_address': server_address,
        'cseq_number': 2,
        'authorization': authorization,
    }
    event.put('send_request', (
        send_frame,
        remote_address,
        second_send_message_template
    ))


def main():
    global server_address
    global remote_address

    server_address = sys.argv[1]
    remote_address = (server_address, 5060)

    event.init()
    event.regist('regist', register_regist)
    event.regist('recv_response', register_recv_response)

    com.init()
    drv.init((server_address, 5061))

    threading.Thread(target=drv.recv, daemon=True).start()
    threading.Thread(target=event.main, daemon=True).start()
    while True:
        cmd()


if __name__ == '__main__':
    main()
