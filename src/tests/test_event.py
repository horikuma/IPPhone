#!/usr/bin/env python3

import pytest
import event

result = []


def stub1(params):
    global result
    result.append(('stub1', params))


def stub2(params):
    global result
    result.append(('stub2', params))


def test_event_once():
    expected = [('stub1', ('first', ))]

    event.init()
    event.regist('a', stub1)
    event.put('a', ('first', ))
    event.exec()

    assert result == expected


def test_event_dual():
    result.clear()

    expected = [('stub1', ('first', )), ('stub1', ('second', ))]

    event.init()
    event.regist('a', stub1)
    event.put('a', ('first', ))
    event.put('a', ('second', ))
    event.exec()
    event.exec()

    assert result == expected


# def test_event_double():
#     expected = [
#         ('stub1', ('first', )),
#         ('stub2', ('first', ))
#     ]

#     event.init()
#     event.regist('*', stub1)
#     event.regist('a', stub2)
#     event.put('a', ('first', ))
#     event.exec()

#     assert result == expected
