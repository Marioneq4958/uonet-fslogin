from setuptools import find_packages, setup

setup(
    name="uonet-fslogin",
    version="0.1.0",
    packages=find_packages(),
    author="Marioneq4958",
    author_email="marioneq4958@gmail.com",
    description="Uonet+ ADFS & CUFS login",
    keywords=["Vulcan", "UONET+", "ADFS", "CUFS", "login",],
    license="MIT",
    url="https://github.com/marioneq4958/uonet-fslogin",
    python_requires=">=3.6,<4.0",
    install_requires=[
        "asyncio", "aiohttp", "bs4", "beautifulsoup4"
    ],
    extras_require={"testing": ["pytest", "python-dotenv"]},
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Polish",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Education",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

