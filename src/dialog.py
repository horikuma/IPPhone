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
            'kind': 'request',
            'method': 'INVITE',
            'local_cseq_number': 0,
            'local_username': user,
            'local_domainname': domain,
            'local_port': port,
            'remote_tag': '',
        })

        self.machine = lib.build_statemachine(self)
        event.regist('recv_request', self.exec)
        event.regist('answer', self.exec)
        self.boot()

    def exec(self, event_id, params):
        self.trigger(event_id, params)

    def init__boot(self):
        self.to_idle()

    def idle__recv_request(self, params):
        recv_frame = params[0]

        if not 'INVITE' == recv_frame.get('method'):
            return
        self.recv_frame_invite = recv_frame

        self.frame.set('local_tag', f';tag={lib.key(36)}')
        self.send_invite_response(self.recv_frame_invite, 180)
        self.to_ring()

    def ring__answer(self, params):
        local_domainname = self.frame.get('local_domainname')
        sdp = rtp.get_sdp(local_domainname)
        self.send_invite_response(self.recv_frame_invite, 200, sdp)
        self.to_comm()

    def comm__recv_request(self, params):
        recv_frame = params[0]

        if 'INVITE' == recv_frame.get('method'):
            self.send_invite_response(recv_frame, 200)
            return

        if not 'BYE' == recv_frame.get('method'):
            return

        send_frame = recv_frame.copy()
        send_frame.update({
            'kind': 'response',
            'response_code': 200,
            'local_tag': self.frame.get('local_tag'),
            'local_username': self.frame.get('local_username'),
            'local_domainname': self.frame.get('local_domainname'),
            'local_port': self.frame.get('local_port'),
            'content_length': 0,
            'body': '',
        })

        event.put('send_response', (
            send_frame,
            self.server_address,
        ))
        self.to_idle()

    def send_invite_response(self, recv_frame, response_code, sdp=None):
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
