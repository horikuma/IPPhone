import pytest
import lib
import re


def test_get_digest():
    key = ':'.join(['REGISTER', 'sip:asterisk@172.19.248.182:5060'])
    expected = '0fc5797f0a1f159f3d38a937f726c3bd'

    result = lib.get_digest(key)
    assert result == expected


def test_parse_message():
    message = '\r\n'.join((
        'REGISTER sip:asterisk@172.19.248.182:5060 SIP/2.0',
        'Via: SIP/2.0/UDP 172.19.248.182:5061;rport;branch=z9hG4bKPj8r3zuDr3OihPEKr.lBRC3oTOnMGLZ1gv',
        'Max-Forwards: 70',
        'From: <sip:6001@172.19.248.182>;tag=zabqXFceFM2bA1aSZv3Z9l8ZgTUBX1dp',
        'To: <sip:6001@172.19.248.182>',
        'Call-ID: JBvkA0faJxAw1OvWwUxs3heCvqbcLV7F',
        'CSeq: 8088 REGISTER',
        'User-Agent: PJSUA v2.10-dev Linux-5.4.72/x86_64/glibc-2.31',
        'Contact: <sip:6001@172.19.248.182:5061;ob>',
        'Expires: 300',
        'Allow: PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS',
        'Content-Length:  0',
        '',
        '',
    ))
    expected = {
        'start-line': 'REGISTER sip:asterisk@172.19.248.182:5060 SIP/2.0',
        'header': {
            'Via': 'SIP/2.0/UDP 172.19.248.182:5061;rport;branch=z9hG4bKPj8r3zuDr3OihPEKr.lBRC3oTOnMGLZ1gv',
            'Max-Forwards': '70',
            'From': '<sip:6001@172.19.248.182>;tag=zabqXFceFM2bA1aSZv3Z9l8ZgTUBX1dp',
            'To': '<sip:6001@172.19.248.182>',
            'Call-ID': 'JBvkA0faJxAw1OvWwUxs3heCvqbcLV7F',
            'CSeq': '8088 REGISTER',
            'User-Agent': 'PJSUA v2.10-dev Linux-5.4.72/x86_64/glibc-2.31',
            'Contact': '<sip:6001@172.19.248.182:5061;ob>',
            'Expires': '300',
            'Allow': 'PRACK, INVITE, ACK, BYE, CANCEL, UPDATE, INFO, SUBSCRIBE, NOTIFY, REFER, MESSAGE, OPTIONS',
            'Content-Length': '0'
        },
        'body': ''
    }
    result = lib.parse_message(message)
    assert result == expected


def test_parse_header():
    header = 'Digest realm="asterisk",nonce="1612524413/8a70ffe177df36117558872417f672f5",opaque="5e0e706065fbdb2f",algorithm=md5,qop="auth"'
    expected = {
        'realm': 'asterisk',
        'nonce': '1612524413/8a70ffe177df36117558872417f672f5',
        'opaque': '5e0e706065fbdb2f',
        'algorithm': 'md5',
        'qop': 'auth'
    }

    result = lib.parse_header(header)
    assert result == expected


@pytest.mark.parametrize(('params', 'expected'), [
    (('Digest realm="asterisk",nonce="1612524413/8a70ffe177df36117558872417f672f5",opaque="5e0e706065fbdb2f",algorithm=md5,qop="auth"',
      {'method': 'REGISTER',
       'username': '6002',
       'password': 'unsecurepassword',
       'cnonce': 'KvbQotVlMy',
       'uri': 'sip:asterisk@172.19.248.182:5060'},
      ),
     '5dc31ccae65364d7245d9679c86eca3e'),
    (('Digest realm="asterisk",nonce="1612525925/6bc70af511339bd0ecac098bc0e14366",opaque="33f05c297647fb24",algorithm=md5,qop="auth"',
      {'method': 'REGISTER',
       'username': '6001',
       'password': 'unsecurepassword',
       'cnonce': 'o6hUNOYm8OJfiIXF3nsiICV5WpRUcN2N',
       'uri': 'sip:asterisk@172.19.248.182:5060'},
      ),
     'c674cf081eca48677c917108a53447cd'),
])
def test_build_authorization(params, expected):
    www_authenticate, config = params

    authorization_config = lib.parse_header(www_authenticate)
    authorization_config.update(config)

    result = lib.build_authorization(authorization_config)
    assert re.search(r'response="([^"]+)', result).group(1) == expected


def test_replace_all():
    expected = 'A <b> C A'
    result = lib.replace_all('<a> <b> <c> <a>', {'a': 'A', 'c': 'C', 'd': 'D'})

    assert result == expected
