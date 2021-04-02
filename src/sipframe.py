import copy
import re

import lib

response_reason = {
    180: 'Ringing',
    200: 'OK',
    486: 'Busy Here',
    487: 'Request Terminated',
}

message_template = {
    'request': {
        'start-line': lambda frame: lib.replace_all('<method> sip:<remote_username>@<remote_domainname> SIP/2.0', frame),
        'Via': lambda frame: lib.replace_all('Via: SIP/2.0/UDP <local_domainname>:<local_port><branch>', frame),
        'From': lambda frame: lib.replace_all('From: <sip:<local_username>@<local_domainname>><local_tag>', frame),
        'To': lambda frame: lib.replace_all('To: <sip:<remote_username>@<remote_domainname>><remote_tag>', frame),
        'CSeq': lambda frame: lib.replace_all('CSeq: <local_cseq_number> <method>', frame),
    },
    'response': {
        'start-line': lambda frame: lib.replace_all('SIP/2.0 <response_code> <response_reason>', frame),
        'Via': lambda frame: lib.replace_all('Via: <via>', frame),
        'From': lambda frame: lib.replace_all('From: <from>', frame),
        'To': lambda frame: lib.replace_all('To: <sip:<local_username>@<local_domainname>><local_tag>', frame),
        'CSeq': lambda frame: lib.replace_all('CSeq: <remote_cseq_number> <method>', frame),
    },
    'common': {
        'Max-Forwards': lambda _: 'Max-Forwards: 70',
        'Call-ID': lambda frame: lib.replace_all('Call-ID: <callid>', frame),
        'User-Agent': lambda _: 'User-Agent: horikuma IPPhone',
        'Contact': lambda frame: lib.replace_all('Contact: <sip:<local_username>@<local_domainname>:<local_port>>', frame),
        'Expires': lambda frame: lib.replace_all('Expires: <expires>', frame),
        'Allow': lambda _: 'Allow: INVITE, ACK, BYE, CANCEL, UPDATE',
        'Authorization': lambda frame: lib.replace_all('Authorization: <authorization>', frame),
        'Content-Type': lambda frame: lib.replace_all('Content-Type: <content_type>', frame),
        'Content-Length': lambda frame: lib.replace_all('Content-Length: <content_length>', frame),
        'body': lambda frame: frame['body'],
    },
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
    'Contact',
}


class SipFrame():
    def __init__(self, source=None):
        if None == source:
            self.frame = {}
        elif str == type(source):
            self.frame = self.parse_message(source)
        elif dict == type(source):
            self.frame = source

    def copy(self):
        return copy.deepcopy(self)

    def get(self, label):
        if label in self.frame:
            return self.frame.get(label)
        if not 'header' in self.frame:
            return None
        return self.frame['header'].get(label)

    def set(self, label, value):
        self.frame[label] = value

    def update(self, value):
        self.frame.update(value)

    def parse_message(self, message):
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
        if 'request' == frame['kind']:
            frame['remote_cseq_number'] = int(remote_cseq_number)
        else:
            frame['local_cseq_number'] = int(remote_cseq_number)
        frame['method'] = method

        frame['callid'] = frame['header']['Call-ID']
        frame['via'] = frame['header']['Via']
        frame['from'] = frame['header']['From']
        if 'request' == frame['kind']:
            user, domain = re.search(
                r'<sip:(\d+)@([\d\.]+)>', frame['from']).groups()
            frame['remote_username'] = user
            frame['remote_domainname'] = domain
            frame['remote_tag'] = re.search(
                r'(;tag=.+)', frame['from']).groups()[0]
        if 'response' == frame['kind']:
            user, domain = re.search(
                r'<sip:(\d+)@([\d\.]+)>', frame['header']['To']).groups()
            frame['remote_username'] = user
            frame['remote_domainname'] = domain
            if ';tag=' in frame['header']['To']:
                frame['remote_tag'] = re.search(
                    r'(;tag=.+)', frame['header']['To']).groups()[0]

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

        template = message_template[self.frame['kind']].copy()
        template.update(message_template['common'])

        header = ''
        headers = default_headers.copy()
        if 'add_header' in frame:
            headers |= frame['add_header']
        if 'remove_header' in frame:
            headers -= frame['remove_header']
        for h in headder_priority:
            if not h in headers:
                continue
            header += template[h](frame) + '\r\n'

        message = '\r\n'.join([
            template['start-line'](frame),
            header,
            template['body'](frame),
        ])
        return message

    def set_request(self, frame, method, sdp, authorization):
        self.frame.update({
            'kind': 'request',
            'method': method,
        })
        if sdp:
            self.frame.update({
                'content_type': 'application/sdp',
                'content_length': len(sdp),
                'add_header': {'Content-Type', 'Content-Length'},
                'body': sdp,
            })
            if authorization:
                self.frame.update({
                    'authorization': authorization,
                    'add_header': {'Content-Type', 'Content-Length', 'Authorization'},
                })
        else:
            self.frame.update({'body': ''})

    def set_response(self, frame, response_code, sdp):
        self.frame.update({
            'kind': 'response',
            'response_code': response_code,
            'response_reason': response_reason[response_code],
            'local_tag': frame.get('local_tag'),
            'local_username': frame.get('local_username'),
            'local_domainname': frame.get('local_domainname'),
            'local_port': frame.get('local_port'),
            'body': '',
        })
        if sdp:
            self.frame.update({
                'content_type': 'application/sdp',
                'content_length': len(sdp),
                'add_header': {'Content-Type', 'Content-Length'},
                'body': sdp,
            })
