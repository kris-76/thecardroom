# [The Card Room](https://thecardroom.io)

The Card Room is a Cardano based NFT platform, a unique gallery of collectable
NFT playing cards, individually minted on the Cardano blockchain.  This codebase
represents a collection of scripts we have created and found useful for minting
NFTs on the Cardano blockchain.

# Prerequisites

These scripts assume that cardano-node, cardano-addresses, cardano-db-sync, and
cardano-wallet are installed and running on the system.  Please see details of
how to install and run these on the input-output-hk github account:
  - [cardano-node](https://github.com/input-output-hk/cardano-node)
  - [cardano-db-sync](https://github.com/input-output-hk/cardano-db-sync)
  - [cardano-addresses](https://github.com/input-output-hk/cardano-addresses)
  - [cardano-wallet](https://github.com/input-output-hk/cardano-wallet)

  These scripts also require the following:
    - cardano-node, cardano-db-sync, cardano-address, and cardano-wallet are
      installed and available on the sytem path.
    - The following environment variables have been set appropriately:
      * CARDANO_NODE_SOCKET_PATH
      * TESTNET_CARDANO_NODE_SOCKET_PATH
      * MAINNET_CARDANO_NODE_SOCKET_PATH

# License

This code is released under the [MIT Opensource License](https://en.wikipedia.org/wiki/MIT_License)
you may use and and modify this code as you see fit.  However, this license and
all copyright attributions must remain in place.

# Commission

TCR has spent a significant amount of time, energy, and money creating this package.
As such, TCR has placed into the code a small comission for ourself.  When an NFT
is minted to an external address the code will also transfer the min utxo value to
the TCR wallet.  Currently this is just 1 ADA.  You can of course remove this
from the code but it will be highly appreciated if you leave it in.

# Conclusion

We at TCR hope you find this software useful.  Feel free to provide suggestions
on feature requests and other ways to improve it.