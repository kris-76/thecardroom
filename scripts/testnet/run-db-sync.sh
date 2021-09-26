#!/usr/bin/sh

export TESTNET_CARDANO_NODE_SOCKET_PATH=/home/ubuntu/cardano/testnet/db/node.socket
export CARDANO_NODE_SOCKET_PATH=$TESTNET_CARDANO_BNODE_SOCKET_PATH
PGPASSFILE=../../cardano-src/cardano-db-sync/config/pgpass-testnet cardano-db-sync --config ../../cardano-src/cardano-db-sync/config/testnet-config.json --socket-path $TESTNET_CARDANO_NODE_SOCKET_PATH --state-dir ../../cardano-src/cardano-db-sync/ledger-state/testnet --schema-dir ../../cardano-src/cardano-db-sync/schema/ >> dbsync_log.txt 2>&1 &
