# -*- coding: utf-8 -*-

from os.path import join, dirname
from setuptools import setup, find_packages

setup(
    name='jobCacheRepairer',
    version='1.0.0',
    description='Приложение для восстановления целостности кэша',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
    author='A.Khromov',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3',
    ],
    packages=find_packages(),
    setup_requires=['nose'],
    test_suite='nose.collector',
    install_requires=[
        'requests ~= 2.0',
        'jobLauncher ~= 1.0',
        'PyYAML ~= 3.0',
    ],
    data_files=[('/etc/opt/jobCacheRepairer', ['etc/log_settings.yaml', 'etc/settings.yaml'])],
    entry_points={
        'console_scripts': ['cache_cleaner=cache_repairer:main'],
    },
)
