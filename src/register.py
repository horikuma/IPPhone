#!/usr/bin/env python3

import event
import lib


class Register:
    def __init__(self, server_address, remote_address):
        self.count = 0
        self.server_address = server_address
        self.remote_address = remote_address
        event.regist('regist', self.regist)
        event.regist('recv_response', self.recv_response)

    def regist(self, params):
        send_frame = {
            'server_address': self.server_address,
            'cseq_number': 1,
            'authorization': '',
        }
        event.put('send_request', (
            send_frame,
            self.remote_address,
        ))

    def recv_response(self, params):
        self.count += 1
        if not 1 == self.count:
            return

        recv_frame = params[0]
        authorization_config = lib.parse_header(
            recv_frame['header']['WWW-Authenticate']
        )
        authorization_config.update({
            'method': 'REGISTER',
            'username': '6002',
            'password': 'unsecurepassword',
            'uri': f'sip:asterisk@{self.server_address}:5060',
        })
        authorization = lib.build_authorization(authorization_config)
        send_frame = {
            'server_address': self.server_address,
            'cseq_number': 2,
            'authorization': authorization,
        }
        event.put('send_request', (
            send_frame,
            self.remote_address,
        ))


def init(server_address, remote_address):
    Register(server_address, remote_address)
