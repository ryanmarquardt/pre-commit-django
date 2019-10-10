from setuptools import setup

setup(
    name="pre-commit-django",
    scripts=["migrations-exist.py"],
    install_requires=["django~=2.2"],
)
