from distutils.core import setup

setup(
    name='SMSGateway',
    version='0.1dev',
    packages=['smsgateway','smsgateway.sources','smsgateway.sources.commands'],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description=open('README.txt').read(),
    install_requires=[
        "emoji"
    ]
)

