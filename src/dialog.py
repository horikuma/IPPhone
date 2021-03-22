#!/usr/bin/env python3

import event
import lib
import rtp
from sipframe import SipFrame


class Dialog:
    def __init__(self, config):
        self.retry_count = 0
        self.server_address = config['server_address']

        user, domain, port = config['local_uri']
        self.frame = SipFrame({
            'local_cseq_number': 0,
            'local_username': user,
            'local_domainname': domain,
            'local_port': port,
            'password': config['password'],
        })

        self.machine = lib.build_statemachine(self)
        event.regist('recv_request', self.exec)
        event.regist('recv_response', self.exec)
        event.regist('answer', self.exec)
        event.regist('hangup', self.exec)
        event.regist('new_call', self.exec)
        self.boot()

    def exec(self, event_id, params):
        self.trigger(event_id, params)

    def init__boot(self):
        self.to_idle()

    def idle__new_call(self, params):
        local_domainname = self.frame.get('local_domainname')
        self.frame.update({
            'callid': f'{lib.key(36)}@{local_domainname}',
            'local_tag': f';tag={lib.key(36)}',
            'remote_username': '6003',
            'remote_domainname': local_domainname,
            'remote_tag': '',
        })
        key = 'local_cseq_number'
        self.frame.set(key, self.frame.get(key) + 1)
        sdp = rtp.get_sdp(local_domainname)
        self.send_request('INVITE', sdp)
        self.to_call()

    def idle__recv_request(self, params):
        recv_frame = params[0]

        if not 'INVITE' == recv_frame.get('method'):
            return

        self.recv_frame_invite = recv_frame.copy()

        self.frame.set('callid', recv_frame.get('callid'))
        self.frame.set('local_tag', f';tag={lib.key(36)}')
        self.frame.set('remote_username', recv_frame.get('remote_username'))
        self.frame.set('remote_domainname',
                       recv_frame.get('remote_domainname'))
        self.frame.set('remote_tag', recv_frame.get('remote_tag'))
        self.send_response(self.recv_frame_invite, 180)
        self.to_ring()

    def call__hangup(self, params):
        self.send_request('CANCEL', branch=False)
        self.to_cancel()

    def call__recv_response(self, params):
        recv_frame = params[0]

        if not 'INVITE' == recv_frame.get('method'):
            return

        response_code = recv_frame.get('response_code')
        if 200 == response_code:
            self.retry_count = 0
            self.frame.set('remote_tag', recv_frame.get('remote_tag'))
            self.send_request('ACK')
            self.to_comm()
        elif 401 == response_code:
            self.retry(params)
        elif 486 == response_code:
            self.frame.set('remote_tag', recv_frame.get('remote_tag'))
            self.send_request('ACK')
            self.to_idle()

    def ring__answer(self, params):
        local_domainname = self.frame.get('local_domainname')
        sdp = rtp.get_sdp(local_domainname)
        self.send_response(self.recv_frame_invite, 200, sdp)
        self.to_comm()

    def ring__hangup(self, params):
        self.send_response(self.recv_frame_invite, 486)
        self.to_idle()

    def ring__recv_request(self, params):
        recv_frame = params[0]

        if not 'CANCEL' == recv_frame.get('method'):
            return

        self.send_response(recv_frame, 200)
        self.send_response(self.recv_frame_invite, 487)
        self.to_idle()

    def comm__hangup(self, params):
        key = 'local_cseq_number'
        self.frame.set(key, self.frame.get(key) + 1)
        self.send_request('BYE')
        self.to_idle()

    def comm__recv_request(self, params):
        recv_frame = params[0]

        if 'INVITE' == recv_frame.get('method'):
            local_domainname = self.frame.get('local_domainname')
            sdp = rtp.get_sdp(local_domainname)
            self.send_response(recv_frame, 200, sdp)
            return

        if not 'BYE' == recv_frame.get('method'):
            return

        self.send_response(recv_frame, 200)
        self.to_idle()

    def cancel__recv_response(self, params):
        recv_frame = params[0]

        if not 'INVITE' == recv_frame.get('method'):
            return

        response_code = recv_frame.get('response_code')
        if 487 == response_code:
            self.frame.set('remote_tag', recv_frame.get('remote_tag'))
            self.send_request('ACK', branch=False)
            self.to_idle()

    def retry(self, params):
        recv_frame = params[0]

        self.retry_count += 1
        if not 1 == self.retry_count:
            return

        authorization_config = recv_frame.get('authenticate')
        local_username = self.frame.get('local_username')
        local_domainname = self.frame.get('remote_domainname')
        authorization_config.update({
            'method': 'INVITE',
            'username': local_username,
            'password': self.frame.get('password'),
            'uri': f'sip:{local_username}@{local_domainname}',
        })
        authorization = lib.build_authorization(authorization_config)

        sdp = rtp.get_sdp(local_domainname)
        self.send_request('INVITE', sdp, authorization)

    def send_request(self, method, sdp=None, authorization=None, branch=True):
        if branch:
            self.frame.set('branch', f';branch=z9hG4bK{lib.key(10)}'),
        send_frame = self.frame.copy()
        send_frame.set_request(self.frame, method, sdp, authorization)
        event.put('send_request', (
            send_frame,
            self.server_address,
        ))

    def send_response(self, recv_frame, response_code, sdp=None):
        send_frame = recv_frame.copy()
        send_frame.set_response(self.frame, response_code, sdp)
        event.put('send_response', (
            send_frame,
            self.server_address,
        ))


def init(config):
    Dialog(config)
