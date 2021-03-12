#!/usr/bin/env python3

def get_sdp(local_domainname):
    return '\r\n'.join([
        'v=0',
        f'o=- 1207507748 1207507748 IN IP4 {local_domainname}',
        's=Asterisk',
        f'c=IN IP4 {local_domainname}',
        't=0 0',
        'm=audio 17104 RTP/AVP 0 101',
        'a=rtpmap:0 PCMU/8000',
        'a=rtpmap:101 telephone-event/8000',
        'a=fmtp:101 0-16',
        'a=ptime:20',
        'a=maxptime:150',
        'a=sendrecv',
    ])


def main():
    pass


def init():
    pass
