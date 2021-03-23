#!/usr/bin/env python3

from rich.console import Console
from rich.panel import Panel

import event

con = Console()


def display(event_id, params):
    dir, frame = event_id[:4], params[0]

    method = frame.get('method')
    cseq_num = frame.get('remote_cseq_number')
    if not cseq_num:
        cseq_num = frame.get('local_cseq_number')

    if 'request' == frame.get('kind'):
        con.print(Panel(f'[{dir}] {method}-{cseq_num}'))
    else:
        rcode = frame.get('response_code')
        con.print(Panel(f'[{dir}] {method}-{cseq_num} ({rcode})'))


def main(event_id, params):
    pass


def init():
    for rs in ['recv', 'send']:
        for rr in ['request', 'response']:
            event.regist(f'{rs}_{rr}', display, event.HIGH)
