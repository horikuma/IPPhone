#!/usr/bin/env python3

import event
import lib
import rtp
from sipframe import SipFrame


class Dialog:
    def __init__(self, config):
        self.server_address = config['server_address']

        user, domain, port = config['local_uri']
        self.frame = SipFrame({
            'local_cseq_number': 0,
            'local_username': user,
            'local_domainname': domain,
            'local_port': port,
        })

        self.machine = lib.build_statemachine(self)
        event.regist('recv_request', self.exec)
        event.regist('answer', self.exec)
        event.regist('hangup', self.exec)
        self.boot()

    def exec(self, event_id, params):
        self.trigger(event_id, params)

    def init__boot(self):
        self.to_idle()

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

    def ring__answer(self, params):
        local_domainname = self.frame.get('local_domainname')
        sdp = rtp.get_sdp(local_domainname)
        self.send_response(self.recv_frame_invite, 200, sdp)
        self.to_comm()

    def ring__recv_request(self, params):
        recv_frame = params[0]

        if not 'CANCEL' == recv_frame.get('method'):
            return

        self.send_response(recv_frame, 200)
        self.send_response(self.recv_frame_invite, 487)
        self.to_idle()

    def comm__hangup(self, params):
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

    def send_request(self, method):
        key = 'local_cseq_number'
        self.frame.set(key, self.frame.get(key) + 1)
        self.frame.set('branch', f';branch=z9hG4bK{lib.key(10)}'),
        send_frame = self.frame.copy()
        send_frame.update({
            'kind': 'request',
            'method': method,
        })
        event.put('send_request', (
            send_frame,
            self.server_address,
        ))

    def send_response(self, recv_frame, response_code, sdp=None):
        send_frame = recv_frame.copy()
        send_frame.update({
            'kind': 'response',
            'response_code': response_code,
            'local_tag': self.frame.get('local_tag'),
            'local_username': self.frame.get('local_username'),
            'local_domainname': self.frame.get('local_domainname'),
            'local_port': self.frame.get('local_port'),
            'body': '',
        })
        if sdp:
            send_frame.update({
                'content_type': 'application/sdp',
                'content_length': len(sdp),
                'add_header': {'Content-Type', 'Content-Length'},
                'body': sdp,
            })
        event.put('send_response', (
            send_frame,
            self.server_address,
        ))


def init(config):
    Dialog(config)
