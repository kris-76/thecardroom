#!/usr/bin/sh

export TESTNET_CARDANO_NODE_SOCKET_PATH=/home/ubuntu/cardano/testnet/db/node.socket
export CARDANO_NODE_SOCKET_PATH=$TESTNET_CARDANO_BNODE_SOCKET_PATH
cardano-node run --config /home/ubuntu/cardano/testnet/testnet-config.json --database-path /home/ubuntu/cardano/testnet/db/ --socket-path $TESTNET_CARDANO_NODE_SOCKET_PATH --host-addr 127.0.0.1 --port 2337 --topology /home/ubuntu/cardano/testnet/testnet-topology.json > node_log.txt 2>&1 &
