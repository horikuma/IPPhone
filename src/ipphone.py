#!/usr/bin/env python3

import os
import sys
import syslog as log
import threading

import com
import dialog
import drv
import event
import register as reg


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
    log.openlog('IPPhone', log.LOG_PERROR)
    log.syslog('開始')

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

    threading.Thread(target=drv.recv, daemon=True).start()
    threading.Thread(target=event.main, daemon=True).start()

    while cmd():
        pass

    log.syslog('終了')
    log.closelog()


if __name__ == '__main__':
    main()
