#!/usr/bin/sh
export MAINNET_CARDANO_NODE_SOCKET_PATH=/home/ubuntu/cardano/mainnet/db/node.socket
export CARDANO_NODE_SOCKET_PATH=$MAINNET_CARDANO_BNODE_SOCKET_PATH
PGPASSFILE=../../cardano-src/cardano-db-sync/config/pgpass-mainnet cardano-db-sync --config ../../cardano-src/cardano-db-sync/config/mainnet-config.yaml --socket-path $MAINNET_CARDANO_NODE_SOCKET_PATH --state-dir ../../cardano-src/cardano-db-sync/ledger-state/mainnet --schema-dir ../../cardano-src/cardano-db-sync/schema/ >> db_sync_log.txt 2>&1 &
