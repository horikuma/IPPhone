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
    if '+a' == c:
        event.put('regist')
    if 'q' == c:
        return False
    return True


def main():
    log.openlog('IPPhone', log.LOG_PERROR)
    log.syslog('開始')

    server_address = os.environ['SERVER_ADDRESS']
    config = {
        'remote_address': (server_address, 5060),
        'server_address': (server_address, 5060),
        'local_address': (server_address, 5061),
        'local_username': '6002',
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
