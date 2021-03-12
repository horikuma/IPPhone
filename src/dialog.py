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
        self.boot()

    def exec(self, event_id, params):
        self.trigger(event_id, params)

    def init__boot(self):
        self.frame = SipFrame()
        self.to_idle()

    def idle__recv_request(self, params):
        recv_frame = params[0]

        if 'INVITE' == recv_frame.get('method'):
            self.frame.set('local_tag', f';tag={lib.key(36)}')
            self.send_invite_200(recv_frame)
            self.to_comm()
            return

    def comm__recv_request(self, params):
        recv_frame = params[0]

        if 'INVITE' == recv_frame.get('method'):
            self.send_invite_200(recv_frame)
            return

        if not 'BYE' == recv_frame.get('method'):
            return

        local_domainname = self.server_address[0]

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

    def send_invite_200(self, recv_frame):
        local_domainname = self.server_address[0]
        body = rtp.get_sdp(local_domainname)

        send_frame = recv_frame.copy()
        send_frame.update({
            'kind': 'response',
            'response_code': 200,
            'local_tag': self.frame.get('local_tag'),
            'local_username': self.frame.get('local_username'),
            'local_domainname': self.frame.get('local_domainname'),
            'local_port': self.frame.get('local_port'),
            'content_type': 'application/sdp',
            'content_length': len(body),
            'add_header': {'Content-Type', 'Content-Length'},
            'body': body,
        })

        event.put('send_response', (
            send_frame,
            self.server_address,
        ))


def init(config):
    Dialog(config)
