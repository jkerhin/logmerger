"""Installs logmerger and prints help text with Python 3.9 - 3.12

TODO: Find a way to verify that logmerger/about.py and README.md have been updated
to match CLI options, so the test is more than a simple "smoke test" like it is now.
"""
import nox

@nox.session(python=["3.9", "3.10", "3.11", "3.12"])
def test(session):
    session.install(".")
    session.run("logmerger", "-h")
