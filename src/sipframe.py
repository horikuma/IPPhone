import copy
import re

import lib

response_reason = {
    200: 'OK',
}

message_template = {
    'request': '\r\n'.join([
        '<method> sip:<remote_domainname>:<remote_port> SIP/2.0',
        'Via: SIP/2.0/UDP <local_domainname>:<local_port><branch>',
        'Max-Forwards: 70',
        'From: <sip:<local_username>@<local_domainname>><local_tag>',
        'To: <sip:<remote_username>@<remote_domainname>><remote_tag>',
        'Call-ID: <callid>',
        'CSeq: <local_cseq_number> <method>',
        'User-Agent: horikuma IPPhone',
        'Contact: <sip:<local_username>@<local_domainname>:<local_port>>',
        'Expires: <expires>',
        'Allow: INVITE, ACK, BYE, CANCEL, UPDATE',
        'Authorization: <authorization>',
        'Content-Length: 0',
        '',
        '',
    ]),
    'response': '\r\n'.join([
        'SIP/2.0 <response_code> <response_reason>',
        'Via: <via>',
        'Max-Forwards: 70',
        'From: <from>',
        'To: <sip:<local_username>@<local_domainname>><local_tag>',
        'Call-ID: <callid>',
        'CSeq: <remote_cseq_number> <method>',
        'User-Agent: horikuma IPPhone',
        'Contact: <sip:<local_username>@<local_domainname>:<local_port>>',
        'Allow: INVITE, ACK, BYE, CANCEL, UPDATE',
        'Content-Type: <content_type>',
        'Content-Length: <content_length>',
        '',
        '<body>',
    ])
}

headder_priority = [
    'Via',
    'Call-ID',
    'From',
    'To',
    'CSeq',
    'Contact',
    'Max-Forwards',
    'Expires',
    'Authorization',
    'Content-Type',
    'Content-Length',
]

default_headers = {
    'Via',
    'Call-ID',
    'From',
    'To',
    'CSeq',
    'Max-Forwards',
}


class SipFrame():
    def __init__(self, source=None):
        if None == source:
            self.frame = {}
        elif str == type(source):
            self.frame = self.to_frame(source)
        elif dict == type(source):
            self.frame = source

    def copy(self):
        return copy.deepcopy(self)

    def get(self, label):
        return self.frame.get(label)

    def to_frame(self, message):
        message_header_raw, message_body_raw = message.split('\r\n\r\n')
        start_line_raw, *message_header_raw = message_header_raw.split('\r\n')

        message_header = {}
        for h in message_header_raw:
            k, v = [x.strip() for x in h.split(':', 1)]
            message_header[k] = v

        frame = {
            'start-line': start_line_raw,
            'header': message_header,
            'body': message_body_raw,
        }

        kind = start_line_raw.split(' ')
        frame['kind'] = ['request', 'response']['SIP/2.0' == kind[0]]

        if 'response' == frame['kind']:
            frame['response_code'] = int(kind[1])

        remote_cseq_number, method = frame['header']['CSeq'].split()
        frame['remote_cseq_number'] = int(remote_cseq_number)
        frame['method'] = method

        frame['callid'] = frame['header']['Call-ID']
        frame['via'] = frame['header']['Via']
        frame['from'] = frame['header']['From']

        www_authenticate = frame['header'].get('WWW-Authenticate')
        if www_authenticate:
            authenticate = {}
            _, params = www_authenticate.split(' ', 1)
            for param in params.replace('"', '').split(','):
                k, v = [x.strip() for x in param.split('=')]
                authenticate[k] = v
            frame['authenticate'] = authenticate

        return frame

    def to_message(self):
        frame = self.frame
        if 'response_code' in frame:
            frame.update({
                'response_reason': response_reason[frame['response_code']],
            })

        template_message = lib.replace_all(
            message_template[self.frame['kind']], frame)
        template_frame = self.to_frame(template_message)

        header = ''
        headers = default_headers.copy()
        if 'add_header' in frame:
            headers |= frame['add_header']
        if 'remove_header' in frame:
            headers -= frame['remove_header']
        for h in headder_priority:
            if not h in headers:
                continue
            if not h in template_frame['header']:
                continue
            if not template_frame['header'][h]:
                continue
            header += f'{h}: {template_frame["header"][h]}\r\n'

        message = '\r\n'.join([
            template_frame['start-line'],
            header,
            template_frame['body'],
        ])
        return message
