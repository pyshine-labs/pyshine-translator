#!/usr/bin/env python3
"""Setup script for pyshine-translator."""
import os
import re
from setuptools import setup, find_packages

def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'src', '__init__.py')
    with open(version_file, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE)
    if match:
        return match.group(1)
    return '1.0.0'

def get_long_description():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    with open(readme_path, 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name='pyshine_translator',
    version=get_version(),
    author='PyShine',
    author_email='python2ai@gmail.com',
    description='Desktop translator with AI support - translate selected text with a global hotkey',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/pyshine-labs/pyshine-translator',
    license='MIT',
    packages=find_packages(),
    package_data={
        '': ['../icons/*.png', '../icons/*.ico'],
    },
    include_package_data=True,
    python_requires='>=3.8',
    install_requires=[
        'PySide6>=6.5.0',
        'googletrans==4.0.0rc1',
        'langdetect>=1.0.9',
        'keyboard>=0.13.5',
        'pyautogui>=0.9.54',
        'pynput>=1.7.6',
        'requests>=2.31.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'build>=0.10.0',
            'twine>=4.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'pyshine-translator=src.tray_app:main',
            'pyshine-translate=src.tray_app:main',
        ],
        'gui_scripts': [
            'pyshine-translator-gui=src.tray_app:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: Qt',
        'Environment :: Win32 (MS Windows)',
        'Environment :: MacOS X',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Utilities',
    ],
    keywords=[
        'translator',
        'translation',
        'ai',
        'ollama',
        'openai',
        'desktop',
        'hotkey',
        'system-tray',
    ],
)
