#!/usr/bin/sh
cardano-node run --config /home/krish/cardano/testnet/testnet-config.json --database-path /home/krish/cardano/testnet/db/ --socket-path $TESTNET_CARDANO_NODE_SOCKET_PATH --host-addr 127.0.0.1 --port 2337 --topology /home/krish/cardano/testnet/testnet-topology.json > node_log.txt 2>&1 &
