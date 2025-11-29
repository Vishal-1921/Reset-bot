from setuptools import setup, find_packages

setup(
    name="reset-bot",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "requests==2.31.0",
        "telethon==1.28.5", 
        "user-agent==0.1.9",
        "cfonts==1.4.0",
        "aiohttp==3.8.5"
    ],
)
