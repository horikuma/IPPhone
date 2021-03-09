#!/usr/bin/env python3

import random
import re
import string
from hashlib import md5

from transitions import Machine


def key(length):
    c = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join([random.choice(c) for i in range(length)])


def get_digest(key):
    return md5(key.encode()).hexdigest()


def build_authorization(config):
    c = {
        'nc': '00000001',  # TODO
        'cnonce': key(10),
    }
    c.update(config)

    # a1 = ユーザ名 ':' realm ':' パスワード
    a1 = ':'.join([c['username'], c['realm'], c['password']])
    # a2 = HTTPのメソッド ':' コンテンツのURI
    a2 = ':'.join([c['method'], c['uri']])
    # response = MD5(MD5(a1) ':' nonce ':' nc ':' cnonce ':' qop ':' MD5(A2))
    c['response'] = get_digest(':'.join([
        get_digest(a1),
        c['nonce'],
        c['nc'],
        c['cnonce'],
        c['qop'],
        get_digest(a2)
    ]))
    template = 'Digest username="<username>", realm="<realm>", uri="<uri>", nonce="<nonce>", nc="<nc>", cnonce="<cnonce>", qop="<qop>", algorithm=<algorithm>, response="<response>", opaque="<opaque>"'
    return replace_all(template, c)


def replace_all(source, config):
    result = source
    for k, v in config.items():
        result = result.replace(f'<{k}>', str(v))
    return result


def build_statemachine(model):
    sm = Machine(
        model=model,
        initial='init',
        ignore_invalid_triggers=True,)

    for symbol in dir(model):
        match = re.match(r'(\w+)__(\w+)', symbol, flags=re.ASCII)
        if not match:
            continue
        # state names in HSMs MUST NOT contain underscores. (TODO)
        state, event = match.groups()
        sm.add_state(state)
        sm.add_transition(
            trigger=event,
            source=state,
            dest=None,
            after=symbol)

    return sm
