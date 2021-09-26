#!/usr/bin/sh

export MAINNET_CARDANO_NODE_SOCKET_PATH=/home/ubuntu/cardano/mainnet/db/node.socket
export CARDANO_NODE_SOCKET_PATH=$MAINNET_CARDANO_BNODE_SOCKET_PATH
cardano-node run --config /home/ubuntu/cardano/mainnet/mainnet-config.json --database-path /home/ubuntu/cardano/mainnet/db/ --socket-path $MAINNET_CARDANO_NODE_SOCKET_PATH --host-addr 127.0.0.1 --port 2338 --topology /home/ubuntu/cardano/mainnet/mainnet-topology.json > node_log.txt 2>&1 &
