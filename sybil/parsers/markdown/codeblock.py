import re
from collections.abc import Iterable
from typing import List, Optional

from markdown_it import MarkdownIt

from sybil import Document, Lexeme, Region
from sybil.parsers.abstract import AbstractCodeBlockParser
from sybil.typing import Evaluator

from ..abstract.codeblock import PythonDocTestOrCodeBlockParser
from ..markdown.lexers import DirectiveInHTMLCommentLexer


def _line_offsets(text: str) -> List[int]:
    """Return the character offset of each line in the text."""
    offsets = [0]
    for i, char in enumerate(text):
        if char == "\n":
            offsets.append(i + 1)
    return offsets


class _MarkdownItFencedCodeBlockLexer:
    """
    A :class:`~sybil.typing.Lexer` for Markdown fenced code blocks using MarkdownIt.
    """

    def __call__(self, document: Document) -> Iterable[Region]:
        md = MarkdownIt()
        md.disable("code")
        tokens = md.parse(src=document.text)
        offsets = _line_offsets(document.text)

        for token in tokens:
            if token.type != "fence":
                continue

            assert token.map is not None
            info_match = re.match(r"^([^\s`]+)", token.info)
            language = info_match.group(1) if info_match else ""
            if not language:
                continue

            start_line, end_line = token.map
            region_start = offsets[start_line]
            if end_line < len(offsets):
                region_end = offsets[end_line] - 1
            else:
                region_end = len(document.text)

            if start_line + 1 < len(offsets):
                source_offset = offsets[start_line + 1] - region_start
            else:
                source_offset = len(document.text) - region_start

            source = Lexeme(token.content, offset=source_offset, line_offset=0)
            yield Region(
                region_start,
                region_end,
                lexemes={
                    "arguments": language,
                    "source": source,
                },
            )


class CodeBlockParser(AbstractCodeBlockParser):
    """
    A :any:`Parser` for :ref:`markdown-codeblock-parser` examples.

    :param language:
        The language that this parser should look for.

    :param evaluator:
        The evaluator to use for evaluating code blocks in the specified language.
        You can also override the :meth:`evaluate` method below.
    """

    def __init__(
        self, language: Optional[str] = None, evaluator: Optional[Evaluator] = None
    ) -> None:
        super().__init__(
            [
                _MarkdownItFencedCodeBlockLexer(),
                DirectiveInHTMLCommentLexer(
                    directive=r"(invisible-)?code(-block)?",
                    arguments=".+",
                ),
            ],
            language,
            evaluator,
        )


class PythonCodeBlockParser(PythonDocTestOrCodeBlockParser):
    """
    A :any:`Parser` for Python :ref:`markdown-codeblock-parser` examples.

    :param future_imports:
        An optional list of strings that will be turned into
        ``from __future__ import ...`` statements and prepended to the code
        in each of the examples found by this parser.

    :param doctest_optionflags:
        :ref:`doctest option flags<option-flags-and-directives>` to use
        when evaluating the doctest examples found by this parser.
    """

    codeblock_parser_class = CodeBlockParser
