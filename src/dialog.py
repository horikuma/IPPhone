#!/usr/bin/env python3

import event
import lib


class Dialog:
    def __init__(self):
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

        print(recv_frame)


def init():
    Dialog()
