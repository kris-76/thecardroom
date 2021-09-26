#!/usr/bin/sh

sudo service postgresql start > db_sync_log.txt
PGPASSFILE=../../cardano-src/cardano-db-sync/config/pgpass-mainnet ../../cardano-src/cardano-db-sync/db-sync-node/bin/cardano-db-sync --config ../../cardano-src/cardano-db-sync/config/mainnet-config.yaml --socket-path $MAINNET_CARDANO_NODE_SOCKET_PATH --state-dir ../../cardano-src/cardano-db-sync/ledger-state/mainnet --schema-dir ../../cardano-src/cardano-db-sync/schema/ >> db_sync_log.txt 2>&1 &
