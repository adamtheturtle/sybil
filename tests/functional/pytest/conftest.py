from __future__ import print_function
from functools import partial
import re
from typing import Iterator, Generator, Optional

import pytest

from sybil import Region, Sybil
from sybil.parsers.rest import PythonCodeBlockParser


@pytest.fixture(scope="function")
def function_fixture() -> Generator[str, None, None]:
    print('function_fixture setup')
    yield 'f'
    print(' function_fixture teardown')


@pytest.fixture(scope="class")
def class_fixture() -> Generator[str, None, None]:
    print('class_fixture setup')
    yield 'c'
    print('class_fixture teardown')


@pytest.fixture(scope="module")
def module_fixture() -> Generator[str, None, None]:
    print('module_fixture setup')
    yield 'm'
    print('module_fixture teardown')


@pytest.fixture(scope="session")
def session_fixture() -> Generator[str, None, None]:
    print('session_fixture setup')
    yield 's'
    print('session_fixture teardown')


def check(letter, example) -> Optional[str]:
    namespace = example.namespace
    for name in (
        'x', 'session_fixture', 'module_fixture',
        'class_fixture', 'function_fixture'
    ):
        print(namespace[name], end='')
    print(end=' ')
    namespace['x'] += 1
    text, expected = example.parsed
    actual = text.count(letter)
    if actual != expected:
        message = '{} count was {} instead of {}'.format(
            letter, actual, expected
        )
        if letter=='X':
            raise ValueError(message)
        return message
    return None


def parse_for(letter, document) -> Iterator[Region]:
    for m in re.finditer(r'(%s+) (\d+) check' % letter, document.text):
        yield Region(m.start(), m.end(),
                     (m.group(1), int(m.group(2))),
                     partial(check, letter))


def sybil_setup(namespace) -> None:
    print('sybil setup', end=' ')
    namespace['x'] = 0


def sybil_teardown(namespace) -> None:
    print('sybil teardown', namespace['x'])


pytest_collect_file = Sybil(
    parsers=[
        partial(parse_for, 'X'),
        partial(parse_for, 'Y'),
        PythonCodeBlockParser(['print_function'])
    ],
    pattern='*.rst',
    setup=sybil_setup, teardown=sybil_teardown,
    fixtures=['function_fixture', 'class_fixture',
              'module_fixture', 'session_fixture']
).pytest()
