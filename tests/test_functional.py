import sys
from os.path import split, join
from unittest.main import main as unittest_main
from unittest.runner import TextTestRunner

from nose.core import run_exit as NoseMain, TextTestRunner as NoseRunner
from pytest import main as pytest_main

functional_test_dir = join(*(split(__file__)[:-2]+('functional_tests', )))


class Finder(object):

    def __init__(self, text):
        self.text = text
        self.index = 0

    def then_find(self, substring):
        assert substring in self.text[self.index:]
        self.index = self.text.index(substring, self.index)


def test_pytest(capsys):

    class CollectResults:
        def pytest_sessionfinish(self, session):
            self.session = session

    results = CollectResults()
    return_code = pytest_main(['-vs', join(functional_test_dir, 'pytest')],
                              plugins=[results])
    assert return_code == 1
    assert results.session.testsfailed == 2
    assert results.session.testscollected == 8

    out, err = capsys.readouterr()
    out = Finder(out)
    out.then_find('fail.rst::line:1,column:1')
    out.then_find('fail.rst sybil setup 0 PASSED')
    out.then_find('fail.rst::line:3,column:1')
    out.then_find('fail.rst 1 FAILED')
    out.then_find('fail.rst::line:5,column:1')
    out.then_find('fail.rst 2 FAILED')
    out.then_find('fail.rst::line:7,column:1')
    out.then_find('fail.rst 3 PASSED sybil teardown 4')
    out.then_find('pass.rst::line:1,column:1')
    out.then_find('pass.rst sybil setup 0 PASSED')
    out.then_find('pass.rst::line:3,column:1')
    out.then_find('pass.rst 1 PASSED')
    out.then_find('pass.rst::line:5,column:1')
    out.then_find('pass.rst 2 PASSED')
    out.then_find('pass.rst::line:7,column:1')
    out.then_find('pass.rst 3 PASSED sybil teardown 4')
    out.then_find('_ fail.rst line=3 column=1 _')
    out.then_find('Y count was 3 instead of 2')
    out.then_find('functional_tests/pytest/fail.rst:3: SybilFailure')
    out.then_find('_ fail.rst line=5 column=1 _')
    out.then_find('ValueError: X count was 3 instead of 4')


def test_unittest(capsys):
    runner = TextTestRunner(verbosity=2, stream=sys.stdout)
    main = unittest_main(
        exit=False, module=None, testRunner=runner,
        argv=['x', 'discover', '-v', join(functional_test_dir, 'unittest')]
    )
    out, err = capsys.readouterr()
    assert err == ''
    out = Finder(out)
    out.then_find('sybil setup')
    out.then_find('fail.rst,line:1,column:1 ... 0\nok')
    out.then_find('fail.rst,line:3,column:1 ... 1\nFAIL')
    out.then_find('fail.rst,line:5,column:1 ... 2\nERROR')
    out.then_find('fail.rst,line:7,column:1 ... 3\nok')
    out.then_find('sybil teardown 4\nsybil setup')
    out.then_find('pass.rst,line:1,column:1 ... 0\nok')
    out.then_find('pass.rst,line:3,column:1 ... 1\nok')
    out.then_find('pass.rst,line:5,column:1 ... 2\nok')
    out.then_find('pass.rst,line:7,column:1 ... 3\nok')
    out.then_find('sybil teardown 4')
    out.then_find('ERROR: ')
    out.then_find('fail.rst,line:5,column:1')
    out.then_find('ValueError: X count was 3 instead of 4')
    out.then_find('FAIL:')
    out.then_find('fail.rst,line:3,column:1')
    out.then_find('Y count was 3 instead of 2')
    out.then_find('Ran 8 tests')
    assert main.result.testsRun == 8
    assert len(main.result.failures) == 1
    assert len(main.result.errors) == 1


def test_nose(capsys):
    class ResultStoringMain(NoseMain):
        def runTests(self):
            self.testRunner = NoseRunner(stream=sys.stdout,
                                         verbosity=self.config.verbosity,
                                         config=self.config)
            self.result = self.testRunner.run(self.test)

    main = ResultStoringMain(
        module=None,
        argv=['x', '-v', join(functional_test_dir, 'nose')]
    )
    assert main.result.testsRun == 9
    assert len(main.result.failures) == 1
    assert len(main.result.errors) == 1

    out, err = capsys.readouterr()
    assert err == ''
    out = Finder(out)
    out.then_find('sybil setup')
    out.then_find('fail.rst,line:1,column:1 ... 0\nok')
    out.then_find('fail.rst,line:3,column:1 ... 1\nFAIL')
    out.then_find('fail.rst,line:5,column:1 ... 2\nERROR')
    out.then_find('fail.rst,line:7,column:1 ... 3\nok')
    out.then_find('sybil teardown 4\nsybil setup')
    out.then_find('pass.rst,line:1,column:1 ... 0\nok')
    out.then_find('pass.rst,line:3,column:1 ... 1\nok')
    out.then_find('pass.rst,line:5,column:1 ... 2\nok')
    out.then_find('pass.rst,line:7,column:1 ... 3\nok')
    out.then_find('sybil teardown 4')
    out.then_find('ERROR: ')
    out.then_find('fail.rst,line:5,column:1')
    out.then_find('ValueError: X count was 3 instead of 4')
    out.then_find('FAIL:')
    out.then_find('fail.rst,line:3,column:1')
    out.then_find('Y count was 3 instead of 2')