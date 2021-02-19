# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['bwprotanalyzer']

package_data = \
{'': ['*']}

entry_points = \
{'console_scripts': ['bwprotanalyzer = bwprotanalyzer.__main__']}

setup_kwargs = {
    'name': 'bwprotanalyzer',
    'version': '1.0.0',
    'description': 'Analysiert eine BWPROT20.DAT-Datei, liest Änderungen und stellt (falls gewünscht) eine lesbare Log-Datei zur Verfügung',
    'long_description': None,
    'author': 'cozyGalvinism',
    'author_email': 'reallifejunkies@googlemail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'entry_points': entry_points,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
