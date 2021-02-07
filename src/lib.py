#!/usr/bin/env python3

import random
import re
import string
from hashlib import md5


def key(length):
    c = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return "".join([random.choice(c) for i in range(length)])


def get_digest(keys):
    return md5(":".join(keys).encode()).hexdigest()


def parse_message(message):
    message_header_raw, message_body_raw = message.split('\r\n\r\n')
    start_line_raw, *message_header_raw = message_header_raw.split('\r\n')

    message_header = {}
    for h in message_header_raw:
        k, v = [x.strip() for x in h.split(":", 1)]
        message_header[k] = v

    result = {
        'start-line': start_line_raw,
        'header': message_header,
        'body': message_body_raw,
    }

    return result


def parse_header(header):
    result = {}
    kind, params = header.split(" ", 1)
    if not "Digest" == kind:
        return result

    for param in params.replace("\"", "").split(","):
        k, v = [x.strip() for x in param.split("=")]
        result[k] = v
    return result


def build_authorization(config):
    c = {
        "nc": "00000001", # TODO
        "cnonce": key(10),
    }
    c.update(config)

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
    template = 'Digest username="<username>", realm="<realm>", uri="<uri>", nonce="<nonce>", nc="<nc>", cnonce="<cnonce>", qop="<qop>", algorithm=<algorithm>, response="<response>", opaque="<opaque>"'
    return replace_all(template, c)


def replace_all(source, config):
    result = source
    for k, v in config.items():
        result = result.replace(f'<{k}>', v)
    return result
