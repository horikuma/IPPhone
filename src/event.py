#!/usr/bin/env python3

import heapq
import queue
import threading

event_queue = None
event_hooks = None

LOW = 30
MIDDLE = 20
HIGH = 10


def regist(event_id, hook, priority=MIDDLE):
    global event_hooks
    if not event_id in event_hooks:
        event_hooks[event_id] = []
    event_hooks[event_id].append((priority, hook))


def put(event_id, params=None, delay=None):
    if not delay:
        event_queue.put((event_id, params))
    else:
        threading.Timer(delay, put, (event_id, params)).start()


def exec():
    event_id, params = event_queue.get()
    if not event_id in event_hooks:
        print(f'404 event_hook not found :{event_id}')
        return

    event_hook = event_hooks[event_id] + event_hooks['*']
    heapq.heapify(event_hook)
    while event_hook:
        _, h = heapq.heappop(event_hook)
        # print(event_id)
        h(event_id, params)


def main():
    while True:
        exec()


def init():
    global event_queue
    global event_hooks

    event_queue = queue.Queue()
    event_hooks = {'*': []}
