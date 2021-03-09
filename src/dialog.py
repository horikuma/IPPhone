#!/usr/bin/env python3

import event
import lib


class Dialog:
    def __init__(self, config):
        self.server_address = config['server_address']
        self.machine = lib.build_statemachine(self)
        event.regist('recv_request', self.exec)
        self.boot()

    def exec(self, event_id, params):
        self.trigger(event_id, params)

    def init__boot(self):
        self.frame = {}
        self.to_idle()

    def idle__recv_request(self, params):
        recv_frame = params[0]

        if 'INVITE' == recv_frame['method']:
            self.frame['local_tag'] = f';tag={lib.key(36)}'
            self.send_invite_200(recv_frame)
            self.to_comm()
            return

    def comm__recv_request(self, params):
        recv_frame = params[0]

        if 'INVITE' == recv_frame['method']:
            self.send_invite_200(recv_frame)
            return

        if not 'BYE' == recv_frame['method']:
            return

        local_domainname = self.server_address[0]

        send_frame = recv_frame.copy()
        send_frame.update({
            'kind': 'response',
            'response_code': 200,
            'local_tag': self.frame['local_tag'],
            'local_username': '6002',
            'local_domainname': local_domainname,
            'local_port': 5061,
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
        body = '\r\n'.join([
            'v=0',
            f'o=- 1207507748 1207507748 IN IP4 {local_domainname}',
            's=Asterisk',
            f'c=IN IP4 {local_domainname}',
            't=0 0',
            'm=audio 17104 RTP/AVP 0 101',
            'a=rtpmap:0 PCMU/8000',
            'a=rtpmap:101 telephone-event/8000',
            'a=fmtp:101 0-16',
            'a=ptime:20',
            'a=maxptime:150',
            'a=sendrecv',
        ])

        send_frame = recv_frame.copy()
        send_frame.update({
            'kind': 'response',
            'response_code': 200,
            'local_tag': self.frame['local_tag'],
            'local_username': '6002',
            'local_domainname': local_domainname,
            'local_port': 5061,
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
