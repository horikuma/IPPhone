#!/usr/bin/env python3

import re
import sys
import threading

import com
import drv
import event
import lib

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
        'authorization': '',
    }
    event.put('send_request', (
        send_frame,
        remote_address,
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
