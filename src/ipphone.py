#!/usr/bin/env python3

import os
import sys
import syslog as log
import threading

import com
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
    remote_address = (server_address, 5060)

    event.init()

    com.init()
    drv.init((server_address, 5061))
    reg.init(server_address, remote_address)

    threading.Thread(target=drv.recv, daemon=True).start()
    threading.Thread(target=event.main, daemon=True).start()

    while cmd():
        pass

    log.syslog('終了')
    log.closelog()


if __name__ == '__main__':
    main()
