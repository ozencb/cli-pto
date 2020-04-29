import os
import re

from setuptools import find_packages, setup


def get_version(package):
    path = os.path.join(os.path.dirname(__file__), package, "__init__.py")
    with open(path, "rb") as f:
        init_py = f.read().decode("utf-8")
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


setup(
    name='cli-pto',
    author='Özenç Bilgili',
    description='A CLI text editor with encryption.',
    version=get_version('cli_pto'),
    url='https://github.com/ozencb/cli-pto',
    packages=find_packages(),
        install_requires=['prompt-toolkit', 'Pygments', 'cryptography'],
        entry_points={'console_scripts': 'cli-pto = cli_pto.clipto:main'},
        license=open('LICENSE').read(),
        keywords=['text', 'editor', 'encryption', 'encrypted', 'password', 'manager']
)
