#!/usr/bin/env python3

import event
import lib

states = ['init', 'idle', 'trying', 'registered']


class Register:
    def __init__(self, server_address, remote_address):
        self.count = 0
        self.server_address = server_address
        self.remote_address = remote_address

        self.machine = lib.build_statemachine(self, states)
        event.regist('regist', self.exec)
        event.regist('recv_response', self.exec)
        self.boot()

    def exec(self, event_id, params):
        self.trigger(event_id, params)

    def init__boot(self):
        self.to_idle()

    def idle__regist(self, params):
        send_frame = {
            'server_address': self.server_address,
            'cseq_number': 1,
        }
        event.put('send_request', (
            send_frame,
            self.remote_address,
        ))
        self.to_trying()

    def trying__recv_response(self, params):
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
            'add_header': {'Authorization', 'Expires', 'Contact'}
        }
        event.put('send_request', (
            send_frame,
            self.remote_address,
        ))
        self.to_registered()


def init(server_address, remote_address):
    Register(server_address, remote_address)
