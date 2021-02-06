import pytest
import lib
import re

def test_get_digest():
    result = lib.get_digest(["REGISTER", "sip:asterisk@172.19.248.182:5060"])
    assert "0fc5797f0a1f159f3d38a937f726c3bd" == result


@pytest.mark.parametrize(("params", "expected"), [
    (('Digest realm="asterisk",nonce="1612524413/8a70ffe177df36117558872417f672f5",opaque="5e0e706065fbdb2f",algorithm=md5,qop="auth"',
      "6002",
      "172.19.248.182",
      "KvbQotVlMy"),
     "5dc31ccae65364d7245d9679c86eca3e"),
    (('Digest realm="asterisk",nonce="1612525925/6bc70af511339bd0ecac098bc0e14366",opaque="33f05c297647fb24",algorithm=md5,qop="auth"',
      "6001",
      "172.19.248.182",
      "o6hUNOYm8OJfiIXF3nsiICV5WpRUcN2N"),
     "c674cf081eca48677c917108a53447cd"),
])
def test_build_authorization(params, expected):
    header, username, server_address, cnonce = params
    result = lib.build_authorization(header, username, server_address, cnonce)
    assert expected == re.search(r"response=\"([^\"]+)", result).group(1)
