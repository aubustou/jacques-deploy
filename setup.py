from setuptools import setup

setup(
    name="jacques-deploy",
    description="Jacques deployment tool for automatized reloading of Python services",
    version="0.1.0",
    author="aubustou",
    author_email="survivalfr@yahoo.fr",
    entry_points={
        "console_scripts": [
            "jacques-deploy = jacques_deploy:main",
        ],
    },
)
