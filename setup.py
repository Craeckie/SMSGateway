# from distutils.core import setup
import setuptools

setuptools.setup(
    name='SMSGateway',
    version='0.7.1.5',
    url="https://github.com/Craeckie/SMSGateway",
    description="Forwards messages via SMS from and to instant messengers",
    packages=setuptools.find_packages(),
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",

    install_requires=[
        'appdirs',
        'arrow',
        'asyncio',
        'bs4',
        'cryptography',
        'fbchat',
        'imapclient',
        'matrix-nio[e2e]',
        'slackclient',
        'telethon',
    ]
)
