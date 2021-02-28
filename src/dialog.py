#!/usr/bin/env python3

import event
import lib

states = ['init', 'idle']


class Dialog:
    def __init__(self):
        self.machine = lib.build_statemachine(self, states)
        event.regist('recv_response', self.exec)
        self.boot()

    def exec(self, event_id, params):
        self.trigger(event_id, params)

    def init__boot(self):
        self.to_idle()

    def idle__recv_request(self, params):
        print(params)


def init():
    Dialog()
