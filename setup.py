import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="NFTMint",
    version="0.0.1",
    author="Kris Henderson",
    author_email="kris.henderson76@gmail.com",
    description="The Card Room NFT Mint and Utilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://thecardroom.io/",
    packages=setuptools.find_packages(),
    python_requires='>=3.8',
    install_requires = [
        'numpy'
        ],
    entry_points={
        'console_scripts': [
            'nftmint = tcr.nftmint:main',
            'nftstatus = tcr.status:main',
            'nftipfs = tcr.ipfs:main',
            'nftbuybot = tcr.buybot:main'
            ],
        },
    data_files = [
        ('testnet', ['testnet.ini']),
        ('mainnet', ['mainnet.ini']),
        ]
)
