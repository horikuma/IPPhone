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


def build_authorization(header, username, server_address, cnonce=""):
    c = {
        "username": username,
        "realm": re.search(r"realm=\"([^\"]+)", header).group(1),
        "password": "unsecurepassword",
        "method": "REGISTER",
        "uri": f"sip:asterisk@{server_address}:5060",
        "nonce": re.search(r"nonce=\"([^\"]+)", header).group(1),
        "nc": "00000001",
        "cnonce": cnonce if cnonce else key(10),
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
