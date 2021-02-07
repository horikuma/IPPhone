#!/usr/bin/env python3

import socket
import sys
import re
import lib

first_send_message_template = """\
REGISTER sip:asterisk@<server_address>:5060 SIP/2.0
Via: SIP/2.0/UDP <server_address>:5061;rport;branch=z9hG4bKPjEMKNT1arBd1xzjzfSCDYJAqS-1U1vqOl
Max-Forwards: 70
From: <sip:6002@<server_address>>;tag=0E5AsBqTALBI8zv1roq682BWtJt6wJOu
To: <sip:6002@<server_address>>
Call-ID: deUH4-p2IpimBfdJvwFAHH8EVJRay1BU
CSeq: <cseq_number> REGISTER
User-Agent: PJSUA v2.10-dev Linux-5.4.72/x86_64/glibc-2.31
Contact: <sip:6002@<server_address>:5061;ob>
Expires: 300
Allow: PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS
Content-Length:  0
"""

second_send_message_template = """\
REGISTER sip:asterisk@<server_address>:5060 SIP/2.0
Via: SIP/2.0/UDP <server_address>:5061;rport;branch=z9hG4bKPjEMKNT1arBd1xzjzfSCDYJAqS-1U1vqOl
Max-Forwards: 70
From: <sip:6002@<server_address>>;tag=0E5AsBqTALBI8zv1roq682BWtJt6wJOu
To: <sip:6002@<server_address>>
Call-ID: deUH4-p2IpimBfdJvwFAHH8EVJRay1BU
CSeq: <cseq_number> REGISTER
User-Agent: PJSUA v2.10-dev Linux-5.4.72/x86_64/glibc-2.31
Contact: <sip:6002@<server_address>:5061;ob>
Expires: 300
Allow: PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS
Authorization: <authorization>
Content-Length:  0
"""


def main():
    server_address = sys.argv[1]
    remote_address = (server_address, 5060)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    send_message = first_send_message_template.replace(
        "<server_address>",
        server_address
    ).replace(
        "<cseq_number>",
        "1"
    )

    print(send_message)
    send_length = sock.sendto(
        send_message.encode(),
        remote_address
    )
    recv_message, recv_address = sock.recvfrom(1024)
    recv_message = recv_message.decode()
    print(recv_message)

    recv_message = lib.parse_message(recv_message)
    authorization_config = lib.parse_header(recv_message["header"]["WWW-Authenticate"])
    authorization_config.update({
        "method": "REGISTER",
        "username": "6002",
        "password": "unsecurepassword",
        "uri": f"sip:asterisk@{server_address}:5060",
    })
    authorization = lib.build_authorization(authorization_config)
    send_message = second_send_message_template.replace(
        "<server_address>",
        server_address
    ).replace(
        "<cseq_number>",
        "2"
    ).replace(
        "<authorization>",
        authorization
    )

    print(send_message)
    send_length = sock.sendto(
        send_message.encode(),
        remote_address
    )
    recv_message, recv_address = sock.recvfrom(1024)
    recv_message = recv_message.decode()
    print(recv_message)

if __name__ == "__main__":
    main()
