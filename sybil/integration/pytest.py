from __future__ import absolute_import

import os
from inspect import getsourcefile
from os.path import abspath
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, Tuple, Optional, Union, TYPE_CHECKING

from _pytest._code.code import TerminalRepr, Traceback, ExceptionInfo
from _pytest import fixtures
from _pytest.fixtures import FuncFixtureInfo
from _pytest._io import TerminalWriter
from _pytest.main import Session
from _pytest.nodes import Collector
from _pytest.python import Module
import pytest

from ..example import SybilFailure
from .. import example

if TYPE_CHECKING:
    from ..sybil import Sybil

PYTEST_VERSION = tuple(int(i) for i in pytest.__version__.split('.'))

source_file = getsourcefile(example)
assert source_file is not None
example_module_path = abspath(source_file)


class SybilFailureRepr(TerminalRepr):

    def __init__(self, item: 'SybilItem', message: str) -> None:
        self.item = item
        self.message = message

    def toterminal(self, tw: TerminalWriter) -> None:
        tw.line()
        for line in self.message.splitlines():
            tw.line(line)
        tw.line()
        tw.write(self.item.parent.name, bold=True, red=True)
        tw.line(":%s: SybilFailure" % self.item.example.line)


class SybilItem(pytest.Item):

    def __init__(self, parent, sybil: 'Sybil', example: example.Example) -> None:
        name = 'line:{},column:{}'.format(example.line, example.column)
        super(SybilItem, self).__init__(name, parent)
        self.example = example
        self.request_fixtures(sybil.fixtures)

    def request_fixtures(self, names: tuple[str]) -> None:
        # pytest fixtures dance:
        fm = self.session._fixturemanager
        closure = fm.getfixtureclosure(names, self)
        initialnames, names_closure, arg2fixturedefs = closure
        fixtureinfo = FuncFixtureInfo(names, initialnames, names_closure, arg2fixturedefs)
        self._fixtureinfo = fixtureinfo
        self.funcargs: Dict[str, Any] = {}
        self._request = fixtures.FixtureRequest(self, _ispytest=True)

    def reportinfo(self) -> Tuple[Union["os.PathLike[str]", str], Optional[int], str]:
        info = '%s line=%i column=%i' % (
            self.fspath.basename, self.example.line, self.example.column
        )
        return self.example.path, self.example.line, info

    def getparent(self, cls):
        if cls is Module:
            return self.parent
        if cls is Session:
            return self.session

    def setup(self) -> None:
        self._request._fillfixtures()
        for name, fixture in self.funcargs.items():
            self.example.namespace[name] = fixture

    def runtest(self) -> None:
        self.example.evaluate()

    if PYTEST_VERSION >= (7, 4, 0):

        def _traceback_filter(self, excinfo: ExceptionInfo[BaseException]) -> Traceback:
            traceback = excinfo.traceback
            traceback_wrapper = traceback.cut(path=example_module_path)
            traceback_entry = traceback_wrapper[1]
            if getattr(traceback_entry, '_rawentry', None) is not None:
                traceback = Traceback(traceback_entry._rawentry)
            return traceback

    else:

        def _prunetraceback(self, excinfo: ExceptionInfo[BaseException]) -> None:
            traceback_wrapper = excinfo.traceback.cut(path=example_module_path)
            traceback_entry = traceback_wrapper[1]
            if getattr(traceback_entry, '_rawentry', None) is not None:
                excinfo.traceback = Traceback(traceback_entry._rawentry, excinfo)

    def repr_failure(
        self,
        excinfo: ExceptionInfo[BaseException],
        style = None,
    ) -> Union[str, TerminalRepr]:
        if isinstance(excinfo.value, SybilFailure):
            return SybilFailureRepr(self, str(excinfo.value))
        return super().repr_failure(excinfo, style)


class SybilFile(pytest.File):

    def __init__(self, *, sybil: 'Sybil', **kwargs: Any) -> None:
        super(SybilFile, self).__init__(**kwargs)
        self.sybil: 'Sybil' = sybil

    def collect(self) -> Iterator[SybilItem]:
        self.document = self.sybil.parse(Path(self.fspath.strpath))
        for example in self.document:
            yield SybilItem.from_parent(self, sybil=self.sybil, example=example)

    def setup(self) -> None:
        if self.sybil.setup is not None:
            self.sybil.setup(self.document.namespace)

    def teardown(self) -> None:
        if self.sybil.teardown is not None:
            self.sybil.teardown(self.document.namespace)


def pytest_integration(*sybils: 'Sybil') -> Callable[[Path, Collector], SybilFile]:

    def pytest_collect_file(file_path: Path, parent: Collector) -> Optional[SybilFile]:
        result: Optional[SybilFile] = None
        for sybil in sybils:
            if sybil.should_parse(file_path):
                result = SybilFile.from_parent(parent, path=file_path, sybil=sybil)
        return result

    return pytest_collect_file
