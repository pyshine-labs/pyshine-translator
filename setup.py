#!/usr/bin/env python3
"""Setup script for pyshine-translator."""
from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

if __name__ == "__main__":
    setup(
        name="pyshine_translator",
        version="1.4.4",
        description="Desktop translator with AI support - translate selected text with a global hotkey",
        long_description=long_description,
        long_description_content_type="text/markdown",
        author="PyShine",
        author_email="python2ai@gmail.com",
        url="https://pyshine.com",
        project_urls={
            "Bug Tracker": "https://github.com/pyshine-labs/pyshine-translator/issues",
            "Source Code": "https://github.com/pyshine-labs/pyshine-translator",
            "Documentation": "https://github.com/pyshine-labs/pyshine-translator#readme",
        },
        packages=["src"],
        package_data={"src": ["../icons/*.png"]},
        include_package_data=True,
        python_requires=">=3.8",
        install_requires=[
            "googletrans>=4.0.0rc1,<5.0.0",
            "langdetect>=1.0.9,<2.0.0",
            "pyautogui>=0.9.54",
            "pynput>=1.7.6,<2.0.0",
            "pyperclip>=1.8.0,<2.0.0",
            "requests>=2.31.0,<3.0.0",
            "Pillow>=9.0.0",
        ],
        extras_require={
            "windows": ["pywin32>=305"],
        },
        entry_points={
            "console_scripts": [
                "pyshine-translator=src.__main__:main",
            ],
            "gui_scripts": [
                "pyshine-translator-gui=src.__main__:main",
            ],
        },
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Environment :: Win32 (MS Windows)",
            "Intended Audience :: End Users/Desktop",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
        ],
    )
