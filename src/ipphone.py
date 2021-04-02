#!/usr/bin/env python3

import os
import sys
import threading
from logging import DEBUG, WARN, basicConfig, getLogger

import com
import dialog
import display
import drv
import event
import register as reg

basicConfig(level=DEBUG)
logger = getLogger(__name__)


def cmd():
    c = input()
    if 'a' == c:
        event.put('answer')
    elif 'h' == c:
        event.put('hangup')
    elif 'm' == c:
        event.put('new_call')
    elif '+a' == c:
        event.put('regist')
    elif 'q' == c:
        return False
    return True


def main():
    logger.debug('IPPhone')
    logger.debug('開始')

    server_address = os.environ['SERVER_ADDRESS']
    config = {
        'server_address': (server_address, 5060),
        'local_uri': ('6002', server_address, 5061),
        'password': 'unsecurepassword',
        'expires': 3600,
    }

    event.init()

    com.init()
    drv.init(config)
    reg.init(config)
    dialog.init(config)
    display.init()

    threading.Thread(target=drv.recv, daemon=True).start()
    threading.Thread(target=event.main, daemon=True).start()

    while cmd():
        pass

    logger.debug('終了')


if __name__ == '__main__':
    main()
