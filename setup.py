import codecs
from os import path
from setuptools import setup, find_packages

read = lambda filepath: codecs.open(filepath, 'r', 'utf-8').read()

setup(
    name='folivora',
    description='Event calendar for Django.',
    long_description=read(path.join(path.dirname(__file__), 'README.rst')),
    version='0.1a1',
    url='http://folivora.apolloner.eu/',
    author='Team rocketDuck',
    author_email='',
    license='BSD',
    packages=find_packages(exclude=['example']),
    include_package_data = True,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
)

