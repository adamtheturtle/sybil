import __future__
import sys
from pathlib import Path
from typing import Any

import pytest
from testfixtures import compare

from sybil import Example, Sybil
from sybil.document import Document
from sybil.parsers.codeblock import PythonCodeBlockParser, CodeBlockParser
from .helpers import check_excinfo, parse, sample_path, check_path, SAMPLE_PATH, add_to_python_path


def test_basic() -> None:
    examples, namespace = parse('codeblock.txt', PythonCodeBlockParser(), expected=7)
    namespace['y'] = namespace['z'] = 0
    examples[0].evaluate()
    assert namespace['y'] == 1
    assert namespace['z'] == 0
    with pytest.raises(Exception) as excinfo:
        examples[1].evaluate()
    compare(examples[1].parsed, expected="raise Exception('boom!')\n", show_whitespace=True)
    assert examples[1].line == 9
    check_excinfo(examples[1], excinfo, 'boom!', lineno=11)
    examples[2].evaluate()
    assert namespace['y'] == 1
    assert namespace['z'] == 1
    examples[3].evaluate()
    assert namespace['bin'] == b'x'
    assert namespace['uni'] == u'x'
    examples[4].evaluate()
    assert 'NoVars' in namespace
    examples[5].evaluate()
    assert namespace['define_this'] == 1
    examples[6].evaluate()
    assert 'YesVars' in namespace
    assert '__builtins__' not in namespace


def test_other_language_composition_pass() -> None:

    def oh_hai(example):
        assert isinstance(example, Example)
        assert 'HAI' in example.parsed

    parser = CodeBlockParser(language='lolcode', evaluator=oh_hai)
    examples, namespace = parse('codeblock.txt', parser, expected=1)

    # We call evaluate() here to make sure that it does not raise an exception.
    # Though `mypy` authors consider it unnecessary to use the return value of
    # a method which is typed to return only `None`, we do it here once to have
    # some safety: https://github.com/python/mypy/issues/6549.
    result = examples[0].evaluate()  # type: ignore[func-returns-value]
    assert result is None


def test_other_language_composition_fail() -> None:
    def oh_noez(example):
        if 'KTHXBYE' in example.parsed:
            raise ValueError('oh noez')

    parser = CodeBlockParser(language='lolcode', evaluator=oh_noez)
    examples, namespace = parse('codeblock.txt', parser, expected=1)
    with pytest.raises(ValueError):
        examples[0].evaluate()


def test_other_language_no_evaluator() -> None:
    parser = CodeBlockParser('foo')
    with pytest.raises(NotImplementedError):
        parser.evaluate(...)


class LolCodeCodeBlockParser(CodeBlockParser):

    language = 'lolcode'

    def evaluate(self, example: Example) -> None:
        if example.parsed != 'HAI\n':
            raise ValueError(repr(example.parsed))


def test_other_language_inheritance() -> None:
    examples, namespace = parse('codeblock_lolcode.txt', LolCodeCodeBlockParser(), expected=2)
    examples[0].evaluate()
    with pytest.raises(ValueError) as excinfo:
        examples[1].evaluate()
    assert str(excinfo.value) == "'KTHXBYE'"


def future_import_checks(*future_imports) -> Any:
    parser = PythonCodeBlockParser(future_imports)
    examples, namespace = parse('codeblock_future_imports.txt', parser, expected=3)
    with pytest.raises(Exception) as excinfo:
        examples[0].evaluate()
    # check the line number of the first block, which is the hardest case:
    check_excinfo(examples[0], excinfo, 'Boom 1', lineno=3)
    with pytest.raises(Exception) as excinfo:
        examples[1].evaluate()
    # check the line number of the second block:
    check_excinfo(examples[1], excinfo, 'Boom 2', lineno=9)
    examples[2].evaluate()
    # check the line number of the third block:
    assert namespace['foo'].__code__.co_firstlineno == 15
    return namespace['foo']


def test_no_future_imports() -> None:
    future_import_checks()


def test_single_future_import() -> None:
    future_import_checks('barry_as_FLUFL')


def test_multiple_future_imports() -> None:
    future_import_checks('barry_as_FLUFL', 'print_function')


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires python3.7 or higher")
def test_functional_future_imports() -> None:
    foo = future_import_checks('annotations')
    # This will keep working but not be an effective test once PEP 563 finally lands:
    assert foo.__code__.co_flags & __future__.annotations.compiler_flag


def test_windows_line_endings(tmp_path: Path) -> None:
    p = tmp_path / "example.txt"
    p.write_bytes(
        b'This is my example:\r\n\r\n'
        b'.. code-block:: python\r\n\r\n'
        b'    from math import cos\r\n'
        b'    x = 123\r\n\r\n'
        b'That was my example.\r\n'
    )
    document = Document.parse(str(p), PythonCodeBlockParser())
    example, = document
    example.evaluate()
    assert document.namespace['x'] == 123


def test_line_numbers_with_options() -> None:
    parser = PythonCodeBlockParser()
    examples, namespace = parse('codeblock_with_options.txt', parser, expected=2)
    with pytest.raises(Exception) as excinfo:
        examples[0].evaluate()
    # check the line number of the first block, which is the hardest case:
    check_excinfo(examples[0], excinfo, 'Boom 1', lineno=6)
    with pytest.raises(Exception) as excinfo:
        examples[1].evaluate()
    # check the line number of the second block:
    check_excinfo(examples[1], excinfo, 'Boom 2', lineno=14)


def test_codeblocks_in_docstrings() -> None:
    sybil = Sybil([PythonCodeBlockParser()])
    with add_to_python_path(SAMPLE_PATH):
        check_path(sample_path('docstrings.py'), sybil, expected=3)
