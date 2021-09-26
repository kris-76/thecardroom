#!/usr/bin/sh

PGPASSFILE=../../cardano-src/cardano-db-sync/config/pgpass-testnet cardano-db-sync --config ../../cardano-src/cardano-db-sync/config/testnet-config.json --socket-path $TESTNET_CARDANO_NODE_SOCKET_PATH --state-dir ../../cardano-src/cardano-db-sync/ledger-state/testnet --schema-dir ../../cardano-src/cardano-db-sync/schema/ >> db_sync_log.txt 2>&1 &
