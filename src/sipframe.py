import re

import lib


class SipFrame():
    def __init__(self, message):
        self.frame = self.parse_message(message)

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
