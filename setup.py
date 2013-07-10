import os
import codecs
from distutils.core import setup


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

def read(*path):
    full_path = os.path.join(PROJECT_ROOT, *path)
    with codecs.open(full_path, 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name='django-staticfilesplus',
    version='0.1dev',
    author='David Evans',
    author_email='d@evans.io',
    url='http://django-staticfilesplus.evans.io',
    packages=['staticfilesplus'],
    license='Apache license',
    long_description=read('README.rst'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
    ],
)
