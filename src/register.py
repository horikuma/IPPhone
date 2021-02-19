#!/usr/bin/env python3

import event
import lib

states = ['init', 'idle', 'trying', 'registered']


class Register:
    def __init__(self, server_address, remote_address):
        self.retry_count = 0
        self.local_cseq_number = 0
        self.server_address = server_address
        self.remote_address = remote_address
        self.expires = 30

        self.machine = lib.build_statemachine(self, states)
        event.regist('regist', self.exec)
        event.regist('recv_response', self.exec)
        event.regist('register_timer', self.exec)
        self.boot()

    def exec(self, event_id, params):
        self.trigger(event_id, params)

    def init__boot(self):
        self.to_idle()

    def idle__regist(self, params):
        self.local_cseq_number += 1
        send_frame = {
            'server_address': self.server_address,
            'cseq_number': self.local_cseq_number,
            'branch': lib.key(10),
            'expires': self.expires,
        }
        event.put('send_request', (
            send_frame,
            self.remote_address,
        ))
        self.to_trying()

    def trying__recv_response(self, params):
        recv_frame = params[0]

        response_code = recv_frame['response_code']
        if 200 == response_code:
            self.retry_count = 0
            expires = recv_frame['header'].get('Expires')
            if expires:
                self.expires = int(expires)
            event.put('register_timer', delay=self.expires // 2)
            self.to_registered()
        if 401 == response_code:
            self.retry(params)

    def retry(self, params):
        recv_frame = params[0]

        self.retry_count += 1
        if not 1 == self.retry_count:
            return

        authorization_config = recv_frame['authenticate']
        authorization_config.update({
            'method': 'REGISTER',
            'username': '6002',
            'password': 'unsecurepassword',
            'uri': f'sip:asterisk@{self.server_address}:5060',
        })
        authorization = lib.build_authorization(authorization_config)
        self.local_cseq_number += 1
        send_frame = {
            'server_address': self.server_address,
            'cseq_number': self.local_cseq_number,
            'branch': lib.key(10),
            'expires': self.expires,
            'authorization': authorization,
            'add_header': {'Authorization', 'Expires', 'Contact'}
        }
        event.put('send_request', (
            send_frame,
            self.remote_address,
        ))

    def registered__register_timer(self, params):
        event.put('regist')
        self.to_idle()


def init(server_address, remote_address):
    Register(server_address, remote_address)
