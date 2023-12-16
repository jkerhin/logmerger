"""Installs logmerger and runs tests with Python 3.9 - 3.12

Use this file with the `nox` tool to run logmerger with all specified versions
of Python. Note that nox is intended to be installed system-wide (e.g. using pipx)
and is intentionally not included in requirements.txt or requirements-dev.txt
For more information about nox, see: https://nox.thea.codes/en/stable/

TODO: Find a way to verify that logmerger/about.py and README.md have been updated
    to match CLI options
"""
import nox

@nox.session(python=["3.9", "3.10", "3.11", "3.12"])
def test(session):
    session.install("-r", "requirements-dev.txt")
    session.install("pytest")
    session.run("pytest")
