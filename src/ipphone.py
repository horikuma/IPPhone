#!/usr/bin/env python3

import socket
from hashlib import md5
import sys
import re
import string
import random

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


def key(length):
    c = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return "".join([random.choice(c) for i in range(length)])


def get_digest(keys):
    return md5(":".join(keys).encode()).hexdigest()


def build_authorization(header, server_address):
    c = {
        "username": "6002",
        "realm": re.search(r"realm=\"([^\"]+)", header).group(1),
        "password": "unsecurepassword",
        "method": "REGISTER",
        "uri": f"sip:asterisk@{server_address}:5060",
        "nonce": re.search(r"nonce=\"([^\"]+)", header).group(1),
        "nc": "00000001",
        "cnonce": key(10),
        "qop": re.search(r"qop=\"([^\"]+)", header).group(1),
        "algorithm": "md5"
    }

    # A1 = ユーザ名 ":" realm ":" パスワード
    a1 = get_digest([c["username"], c["realm"], c["password"]])
    # A2 = HTTPのメソッド ":" コンテンツのURI
    a2 = get_digest([c["method"], c["uri"]])
    # response = MD5( MD5(A1) ":" nonce ":" nc ":" cnonce ":" qop ":" MD5(A2) )
    c["response"] = get_digest([
        a1,
        c["nonce"],
        c["nc"],
        c["cnonce"],
        c["qop"],
        a2
    ])
    authorization_keys = [
        "username",
        "realm",
        "uri",
        "nonce",
        "nc",
        "cnonce",
        "qop",
        "algorithm",
        "response",
    ]
    return "Digest " + ", ".join([f"{k}=\"{c[k]}\"" for k in authorization_keys])


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
    print(recv_message.decode())

    www_authenticate = re.search(
        r"WWW-Authenticate: ([^\r\n]+)",
        recv_message.decode()
    ).group(1)
    authorization = build_authorization(www_authenticate, server_address)
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
    print(recv_message.decode())

if __name__ == "__main__":
    main()
