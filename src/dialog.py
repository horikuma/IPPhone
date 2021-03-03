#!/usr/bin/env python3

import event
import lib


class Dialog:
    def __init__(self, server_address):
        self.server_address = server_address
        self.machine = lib.build_statemachine(self)
        event.regist('recv_request', self.exec)
        self.boot()

    def exec(self, event_id, params):
        self.trigger(event_id, params)

    def init__boot(self):
        self.to_idle()

    def idle__recv_request(self, params):
        recv_frame = params[0]

        if not 'INVITE' == recv_frame['method']:
            return

        send_frame = recv_frame.copy()
        send_frame['header']['To'] += f';tag={lib.key(36)}'

        message = '\r\n'.join([
            'SIP/2.0 200 OK',
            '\r\n'.join(
                [f'{k}: {v}' for k, v in send_frame['header'].items()]),
            '',
        ])

        event.put('send_response', (
            message,
            self.server_address,
        ))


def init(server_address):
    Dialog(server_address)
