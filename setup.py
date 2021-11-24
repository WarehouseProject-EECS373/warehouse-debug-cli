from setuptools import setup


setup(
    name="warehouse debug cli",
    description="Tool for testing and interacting with warehouse components",
    author="Roberts Kalnins",
    author_email="rkalnins@umich.edu",
    url="www.github.com/",
    packages=["wdc", "wdc.cli", "wdc.targets", "pystcp"], 
)
