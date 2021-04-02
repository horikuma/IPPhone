#!/usr/bin/env python3

import heapq
import inspect
import queue
import re
import threading
from logging import getLogger

logger = getLogger(__name__)

event_queue = None
event_hooks = None

LOW = 30
MIDDLE = 20
HIGH = 10


def regist(event_id, hook, priority=MIDDLE):
    global event_hooks
    if not event_id in event_hooks:
        event_hooks[event_id] = []
    event_hooks[event_id].append(
        (priority, hook.__module__, hook.__name__, hook))
    logger.debug(f'イベントハンドラ登録:{event_id}')


def put(event_id, params=None, delay=None, put_from=None, send_to=None):
    if not put_from:
        filepath = inspect.currentframe().f_back.f_code.co_filename
        filename = re.search(r'([^/]+).py', filepath).group(1)
        funcname = inspect.getframeinfo(inspect.currentframe().f_back).function
        put_from = f'{filename}.{funcname}'
    if not delay:
        event_queue.put((event_id, params, put_from, send_to))
    else:
        threading.Timer(delay, put,
                        (event_id, params, None, put_from, send_to)).start()


def exec():
    event_id, params, put_from, send_to = event_queue.get()
    if not event_id in event_hooks:
        logger.debug(f'イベントフック未登録:{event_id}')
        return

    event_hook = event_hooks[event_id] + event_hooks['*']
    heapq.heapify(event_hook)
    while event_hook:
        *_, h = heapq.heappop(event_hook)
        if send_to and (send_to == '*' or not send_to == h):
            continue
        logger.debug(
            f'event_id: {event_id} ({put_from} -> {h.__module__}.{h.__name__})')
        h(event_id, params)


def main():
    while True:
        exec()


def init():
    global event_queue
    global event_hooks

    event_queue = queue.Queue()
    event_hooks = {'*': []}
