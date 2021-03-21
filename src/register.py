#!/usr/bin/env python3

import event
import lib
from sipframe import SipFrame


class Register:
    def __init__(self, config):
        self.retry_count = 0
        self.server_address = config['server_address']

        user, domain, port = config['local_uri']
        self.frame = SipFrame({
            'kind': 'request',
            'method': 'REGISTER',
            'local_cseq_number': 0,
            'local_username': user,
            'local_domainname': domain,
            'local_port': port,
            'remote_username': user,
            'remote_domainname': domain,
            'remote_port': port,
            'remote_tag': '',
            'expires': config['expires'],
            'callid': f'{lib.key(36)}@{domain}',
            'password': config['password'],
        })

        self.machine = lib.build_statemachine(self)
        event.regist('regist', self.exec)
        event.regist('recv_response', self.exec)
        event.regist('register_timer', self.exec)
        self.boot()

    def exec(self, event_id, params):
        self.trigger(event_id, params)

    def init__boot(self):
        self.to_idle()

    def idle__regist(self, params):
        local_cseq_number = self.frame.get('local_cseq_number')
        self.frame.set('local_cseq_number', local_cseq_number + 1)
        send_frame = self.frame.copy()
        send_frame.update({
            'branch': f';branch=z9hG4bK{lib.key(10)}',
            'local_tag': f';tag={lib.key(36)}',
            'body': '',
        })
        event.put('send_request', (
            send_frame,
            self.server_address,
        ))
        self.to_trying()

    def trying__recv_response(self, params):
        recv_frame = params[0]

        if not 'REGISTER' == recv_frame.get('method'):
            return

        response_code = recv_frame.get('response_code')
        if 200 == response_code:
            self.retry_count = 0
            expires = recv_frame.get('Expires')
            if expires:
                self.frame.set('expires', int(expires))
            event.put('register_timer', delay=int(expires) // 2)
            self.to_registered()
        if 401 == response_code:
            self.retry(params)

    def retry(self, params):
        recv_frame = params[0]

        self.retry_count += 1
        if not 1 == self.retry_count:
            return

        rd = self.frame.get('remote_domainname')
        rp = self.frame.get('remote_port')
        authorization_config = recv_frame.get('authenticate')
        authorization_config.update({
            'method': 'REGISTER',
            'username': self.frame.get('local_username'),
            'password': self.frame.get('password'),
            'uri': f'sip:{rd}:{rp}',
        })
        authorization = lib.build_authorization(authorization_config)
        local_cseq_number = self.frame.get('local_cseq_number')
        self.frame.set('local_cseq_number', local_cseq_number + 1)
        send_frame = self.frame.copy()
        send_frame.update({
            'branch': f';branch=z9hG4bK{lib.key(10)}',
            'local_tag': f';tag={lib.key(36)}',
            'authorization': authorization,
            'add_header': {'Authorization', 'Expires'},
            'body': '',
        })
        event.put('send_request', (
            send_frame,
            self.server_address,
        ))

    def registered__register_timer(self, params):
        event.put('regist')
        self.to_idle()


def init(config):
    Register(config)
