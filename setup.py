"""Setup the package."""
from setuptools import setup, find_packages
import versioneer

with open('README.rst') as readme:
    long_description = readme.read()

setup(
    name='sensor-feed',
    packages=find_packages(),
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),

    description="Simple source/sink sensor feed.",
    long_description=long_description,
    author="David Kent",
    author_email="davidkent@fastmail.com.au",
    url="https://github.com/dmkent/sensor-feed/"
    license="MIT",
)
