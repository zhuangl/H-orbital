"""Setuptools fallback for environments with older pip tooling.

This file keeps installation straightforward on systems where editable
installation from ``pyproject.toml`` is limited.
"""

from setuptools import find_packages, setup


setup(
    name="h-orbital",
    version="1.5.1",
    description="Analytic hydrogen orbital slice visualizer",
    packages=find_packages(include=["h_orbital", "h_orbital.*"]),
    python_requires=">=3.10",
    install_requires=["numpy>=1.24", "scipy>=1.10", "matplotlib>=3.7"],
    extras_require={"dev": ["pytest>=7.4"]},
    entry_points={
        "console_scripts": [
            "H-orbital=h_orbital.cli:main",
            "H-orbital-ui=h_orbital.gui:main",
        ]
    },
)
