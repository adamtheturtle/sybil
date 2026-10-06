Test runner integration
=======================

Sybil aims to integrate with all major Python test runners. Those currently
catered for explicitly are listed below, but you may find that one of these
integration methods will work as required with other test runners.
If not, please file an issue on GitHub.

To show how the integration options work, the following documentation examples
will be tested. They use :ref:`doctests <doctest-simple-testfile>`,
:rst:dir:`code blocks <code-block>` and require a temporary directory:

.. literalinclude:: examples/integration/docs/example.rst
  :language: rest

.. _pytest_integration:

pytest
~~~~~~

You should install Sybil with the ``pytest`` extra, to ensure
you have a compatible version of `pytest`__:

__ https://docs.pytest.org

.. code-block:: bash

  pip install sybil[pytest]

To have `pytest`__ check the examples, Sybil makes use of the
``pytest_collect_file`` hook. To use this, configuration is placed in
a ``confest.py`` in your documentation source directory, as shown below.
``pytest`` should be invoked from a location that has the opportunity to
recurse into that directory:

__ https://docs.pytest.org

.. literalinclude:: examples/integration/docs/conftest.py

The file glob passed as ``pattern`` should match any documentation source
files that contain examples which you would like to be checked.

As you can see, if your examples require any fixtures, these can be requested
by passing their names to the ``fixtures`` argument of the
:class:`~sybil.Sybil` class.
These will be available in the :class:`~sybil.Document`
:class:`~sybil.Document.namespace` in a way that should feel natural
to ``pytest`` users.

The ``setup`` and ``teardown`` parameters can still be used to pass
:class:`~sybil.Document` setup and teardown callables.

The ``path`` parameter, however, is ignored.


.. note::

    pytest provides its own doctest plugin, which can cause problems. It
    should be disabled by including the following in your pytest configuration file:

    .. literalinclude:: examples/quickstart/pytest.ini
        :language: ini


Run example tests
-----------------

If you need to demonstrate that a pytest fixture and test work correctly, you can use
:func:`~sybil.testing.run_pytest` to run them in-process from within a documentation example:

.. literalinclude:: examples/run_pytest/example.rst
    :language: rst

More than one test can be passed. Multiple fixtures can be used, including internal ones such
as :any:`tmp_path <pytest:tmp_path>`, but they must be explicitly specified.

.. _unitttest_integration:

unittest
~~~~~~~~

To have :ref:`unittest-test-discovery` check the example, Sybil makes use of
the `load_tests protocol`__. As such, the following should be placed in a test
module, say ``test_docs.py``, where the unit test discovery process can find it:

__ https://docs.python.org/3/library/unittest.html#load-tests-protocol

.. literalinclude:: examples/integration/unittest/test_docs.py

The ``path`` parameter gives the path, relative to the file containing this
code, that contains the documentation source files.

The file glob passed as ``pattern`` should match any documentation source
files that contain examples which you would like to be checked.

Any setup or teardown necessary for your tests can be carried out in
callables passed to the ``setup`` and ``teardown`` parameters,
which are both called with the :class:`~sybil.Document`
:class:`~sybil.Document.namespace`.

The ``fixtures`` parameter is ignored.

.. _karva_integration:

Karva (experimental)
--------------------

Install Sybil with the ``karva`` extra to use this integration.
Karva currently collects Python source definitions, so this integration generates
native Python modules before the run instead of installing a collection hook.

Export a ``Sybil`` or ``SybilCollection`` from an importable module, such as
``conftest.py``.
Call :meth:`~sybil.Sybil.karva` with ``reference='conftest:sybil'``, explicit documentation
``paths``, and an empty ``destination`` directory inside the project.
The reference must name the same configuration on which the method is called.
The return value is a tuple of generated module paths.
The :func:`~sybil.integration.karva.generate_karva_tests` helper accepts the same
arguments when loading the configuration solely from its reference is convenient.

Run ``uv run karva test <destination>`` from the project root while the generated
modules exist.
Using a temporary directory inside the project keeps ancestor ``conftest.py``
fixtures available and permits automatic removal of the generated files.
Specify source paths explicitly rather than traversing a virtual environment.

Each document becomes one module with one dynamically parametrized test function.
Each example is reported separately, in source order, in the same worker as the
other examples from that document.
The document namespace, setup and teardown callbacks, function fixture injection,
module fixture lifetime, skip behavior, and cleanup after example failures are
preserved.
``unittest.SkipTest`` is translated into a native Karva skip.
Parser and evaluator implementations do not need to change.

This is experimental and does not yet provide full parity with :meth:`~sybil.Sybil.pytest`.
Collection members must select disjoint files.
Overlapping configurations are rejected rather than changing module fixture
lifetimes for the same file.
Fixture names must be Python identifiers other than ``_sybil_example`` and
``_sybil_document``.
Karva's primary diagnostic points to the generated wrapper, although the example
identifier and Sybil failure include the original document path, line and column.
Temporary paths prevent useful reuse of test history across runs.
Selecting a later example does not recreate the namespace established by earlier
examples, and retries may repeat namespace mutations.
Use complete document runs without retries while testing this integration, and
keep your existing runner validation alongside the Karva run.
Native source reporting is tracked in
`Karva issue 1513 <https://github.com/MatthewMckee4/karva/issues/1513>`_.

.. autofunction:: sybil.integration.karva.generate_karva_tests
