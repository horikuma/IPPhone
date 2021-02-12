#!/usr/bin/env python3

import sys
import threading

import com
import drv
import event
import register as reg


def cmd():
    c = input()
    if '+a' == c:
        event.put('regist')
    if 'exit' == c:
        exit()


def main():
    server_address = sys.argv[1]
    remote_address = (server_address, 5060)

    event.init()

    com.init()
    drv.init((server_address, 5061))
    reg.init(server_address, remote_address)

    threading.Thread(target=drv.recv, daemon=True).start()
    threading.Thread(target=event.main, daemon=True).start()
    while True:
        cmd()


if __name__ == '__main__':
    main()
