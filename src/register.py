#!/usr/bin/env python3

import event
import lib

states = ['init', 'idle', 'trying', 'registered']


class Register:
    def __init__(self, server_address, remote_address):
        self.retry_count = 0
        self.frame = {
            'method': 'REGISTER',
            'local_cseq_number': 0,
            'local_username': '6002',
            'local_domainname': server_address,
            'remote_username': '6002',
            'remote_domainname': server_address,
            'remote_tag': '',
            'server_address': server_address,
            'remote_address': remote_address,
            'expires': 30,
            'callid': f'{lib.key(36)}@{server_address}',
        }

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
        self.frame['local_cseq_number'] += 1
        send_frame = self.frame.copy()
        send_frame.update({
            'branch': lib.key(10),
            'local_tag': f';tag={lib.key(36)}',
        })
        print(send_frame)
        event.put('send_request', (
            send_frame,
            self.frame['remote_address'],
        ))
        self.to_trying()

    def trying__recv_response(self, params):
        recv_frame = params[0]

        response_code = recv_frame['response_code']
        if 200 == response_code:
            self.retry_count = 0
            expires = recv_frame['header'].get('Expires')
            if expires:
                self.frame['expires'] = int(expires)
            event.put('register_timer', delay=int(expires) // 2)
            self.to_registered()
        if 401 == response_code:
            self.retry(params)

    def retry(self, params):
        recv_frame = params[0]

        self.retry_count += 1
        if not 1 == self.retry_count:
            return

        server_address = self.frame['server_address']
        authorization_config = recv_frame['authenticate']
        authorization_config.update({
            'method': 'REGISTER',
            'username': self.frame['local_username'],
            'password': 'unsecurepassword',
            'uri': f'sip:asterisk@{server_address}:5060',
        })
        authorization = lib.build_authorization(authorization_config)
        self.frame['local_cseq_number'] += 1
        send_frame = self.frame.copy()
        send_frame.update({
            'branch': lib.key(10),
            'local_tag': f';tag={lib.key(36)}',
            'authorization': authorization,
            'add_header': {'Authorization', 'Expires', 'Contact'},
        })
        event.put('send_request', (
            send_frame,
            self.frame['remote_address'],
        ))

    def registered__register_timer(self, params):
        event.put('regist')
        self.to_idle()


def init(server_address, remote_address):
    Register(server_address, remote_address)
