# Server Setup [The Card Room](https://thecardroom.io)

This describes the steps to take setting up a server from scratch.  These setup
instructions assume running on an Ubuntu server in an Amazon EC2 instance.  With
slight modification it should also work in other linux environments, such as
Windows 10 WSL2


## 1.  Update The Server & Install Prerequisites

  - sudo apt update
  - sudo apt upgrade
  - sudo apt install tree
  - sudo apt install postgresql postgresql-contrib
  - sudo apt install multitail
  - sudo apt install python3-pip
  - sudo apt install libpq-dev
  - pip install psycopg2
  - pip install numpy
  - pip install pillow


## 2.  Install Cardano Binaries

  - https://hydra.iohk.io/job/Cardano/cardano-node/cardano-node-linux/latest-finished
  - https://hydra.iohk.io/job/Cardano/cardano-db-sync/cardano-db-sync-linux/latest-finished


  - cd ~
  - mkdir cardano-bin
  - cd cardano-bin
  - curl https://hydra.iohk.io/build/7872177/download/1/cardano-node-1.30.0-linux.tar.gz --output cardano-node-1.30.0-linux.tar.gz
  - curl https://hydra.iohk.io/build/7857352/download/1/cardano-db-sync-11.0.4-linux.tar.gz --output cardano-db-sync-11.0.4-linux.tar.gz
  - curl https://github.com/input-output-hk/cardano-addresses/releases/download/3.6.0/cardano-addresses-3.6.0-linux64.tar.gz --output cardano-addresses-3.6.0-linux64.tar.gz
  - tar --ungzip -xvf cardano-node-1.30.0-linux.tar.gz
  - tar --ungzip -xvf cardano-db-sync-11.0.0-linux.tar.gz
  - tar --ungzip -xvf cardano-addresses-3.6.0-linux64.tar.gz
  - Edit ~/.profile and add:
    * PATH=$PATH:/home/ubuntu/cardano-bin
    * export TESTNET_CARDANO_NODE_SOCKET_PATH="/home/ubuntu/cardano/testnet/db/node.socket"
    * export MAINNET_CARDANO_NODE_SOCKET_PATH="/home/ubuntu/cardano/mainnet/db/node.socket"
    * export CARDANO_NODE_SOCKET_PATH=$MAINNET_CARDANO_NODE_SOCKET_PATH


## 3.  Setup Configuration for Node and DB Sync

  - mkdir ~/cardano
  - mkdir ~/cardano/mainnet
  - mkdir ~/cardano/mainnet/db
  - mkdir ~/cardano/testnet
  - mkdir ~/cardano/testnet/db


## 4.  Get the Source

  - mkdir ~/workspace
  - cd ~/workspace
  - git clone https://github.com/kris-76/thecardroom.git
  - mkdir ~/cardano-src
  - cd ~/cardano-src
  - git clone https://github.com/input-output-hk/cardano-node.git
  - git clone https://github.com/input-output-hk/cardano-db-sync.git

## 5.  Copy Configuration & Scripts

Note that configuration files for mainnet and testnet are included in
~/workspace/thecardroom/scripts/mainnet and ~/workspace/thecardroom/scripts/testnet
However, it's best to use the configuration files download with the binaries.

  - cp ~/cardano-bin/configuration/cardano/mainnet-alonzo-genesis.json ~/cardano/mainnet/
  - cp ~/cardano-bin/configuration/cardano/mainnet-byron-genesis.json ~/cardano/mainnet/
  - cp ~/cardano-bin/configuration/cardano/mainnet-config.json ~/cardano/mainnet/
  - cp ~/cardano-bin/configuration/cardano/mainnet-shelley-genesis.json ~/cardano/mainnet/
  - cp ~/cardano-bin/configuration/cardano/mainnet-topology.json ~/cardano/mainnet/
  - cp ~/workspace/thecardroom/scripts/mainnet/network-magic.txt ~/cardano/mainnet
  - cp ~/workspace/thecardroom/scripts/mainnet/run-node.sh ~/cardano/mainnet
  - cp ~/workspace/thecardroom/scripts/mainnet/run-db-sync.sh ~/cardano/mainnet
  - cp ~/workspace/thecardroom/scripts/mainnet/tail-logs.sh ~/cardano/mainnet

Make sure the files are executable

  - chmod 755 ~/cardano/mainnet/run-node.sh
  - chmod 755 ~/cardano/mainnet/run-db-sync.sh
  - chmod 755 ~/cardano/mainnet/tail-logs.sh


Optional, repeat for testnet:

  - cp ~/workspace/thecardroom/scripts/testnet/testnet-alonzo-genesis.json ~/cardano/testnet/
  - cp ~/workspace/thecardroom/scripts/testnet/testnet-byron-genesis.json ~/cardano/testnet/
  - cp ~/workspace/thecardroom/scripts/testnet/testnet-config.json ~/cardano/testnet/
  - cp ~/workspace/thecardroom/scripts/testnet/testnet-db-sync-config.json ~/cardano/testnet/
  - cp ~/workspace/thecardroom/scripts/testnet/testnet-shelley-genesis.json ~/cardano/testnet/
  - cp ~/workspace/thecardroom/scripts/testnet/testnet-topology.json ~/cardano/testnet/
  - cp ~/workspace/thecardroom/scripts/testnet/network-magic.txt ~/cardano/testnet
  - cp ~/workspace/thecardroom/scripts/testnet/run-node.sh ~/cardano/testnet
  - cp ~/workspace/thecardroom/scripts/testnet/run-db-sync.sh ~/cardano/testnet
  - cp ~/workspace/thecardroom/scripts/testnet/tail-logs.sh ~/cardano/testnet

Make sure the files are executable

  - chmod 755 ~/cardano/testnet/run-node.sh
  - chmod 755 ~/cardano/testnet/run-db-sync.sh
  - chmod 755 ~/cardano/testnet/tail-logs.sh


## 6.  Setup Databases

  - sudo -i -u postgres
  - createuser --createdb --superuser ubuntu
  - psql
  - ALTER USER ubuntu WITH PASSWORD 'cardano';
  - \du
  - exit
  - exit
  - cd ~/cardano-src/cardano-db-sync
  - chmod 600 config/pgpass-mainnet
  - PGPASSFILE=config/pgpass-mainnet scripts/postgresql-setup.sh --createdb
  - chmod 600 config/pgpass-testnet
  - PGPASSFILE=config/pgpass-testnet scripts/postgresql-setup.sh --createdb

Make sure you have the same version of db-sync source as version of the binary
file that was installed:
  - cardano-db-sync --version
    > cardano-db-sync 11.0.0 - linux-x86_64 - ghc-8.10<br>
    > git revision e2d5cf8068c030ed3c8006ce008b4100fbaad581<br>
  - cd ~/cardano-src/cardano-db-sync
  - git checkout e2d5cf8068c030ed3c8006ce008b4100fbaad581

Run and Configure the database to run on startup
  - sudo systemctl enable postgresql
  - sudo service postgresql start


## 7.  Setup cardano node and dbsync to run on startup
  - sudo cp ~/workspace/thecardroom/scripts/init.d/cardano-* /etc/init.d
  - Review scripts in init.d and ~/workspace/thecardroom/scripts/mainnet to see
    if any changes are needed for your environment.  Usernames, passwords, path,
    installation directory, etc.
  - sudo update-rc.d cardano-node-mainnet defaults
  - sudo systemctl enable cardano-node-mainnet
  - sudo service cardano-node-mainnet start
  - sudo update-rc.d cardano-dbsync-mainnet defaults
  - sudo systemctl enable cardano-dbsync-mainnet
  - sudo service cardano-dbsync-mainnet start

Optional, repeat for testnet
  - sudo update-rc.d cardano-node-testnet defaults
  - sudo service cardano-node-testnet start
  - sudo update-rc.d cardano-dbsync-testnet defaults
  - sudo service cardano-dbsync-testnet start


## 8.  Final Setup

  - cd ~/workspace/thecardroom
  - review testnet.ini
  - review mainnet.ini
  - mkdir log
  - mkdir log/mainnet
  - mkdir log/testnet


## 9.  Test

Downloading the Cardano blockchain and populating the database can take 24 hours
or more.  Even after synchronization is complete it can take several minutes or
even an hour to resync and update the node / database.  Status can be checked by
verifying the cardano-node and cardano-db-sync processes are running with
'ps -aef' or the 'top' command.  Output can be viewed by running 'tail-logs.sh'
in ~/cardano/mainnet.  Once everything is verified to be running, final test can
be done by running the status script:

  - python3 status.py --network=mainnet

If you see some output that looks like this then everything was successful:<br>
> Log File: log/mainnet/status_1632631755.log<br>
> 2021-09-26 04:49:15,559:INFO:mainnet: Database Chain Metadata: 2017-09-23 21:44:51 / mainnet<br>
> 2021-09-26 04:49:15,559:INFO:mainnet: Database Size: 12 GB<br>
> 2021-09-26 04:49:15,559:INFO:mainnet: Cardano Node Tip Slot: 38829215<br>
> 2021-09-26 04:49:15,559:INFO:mainnet:  Database Latest Slot: 24107986<br>
> 2021-09-26 04:49:15,559:INFO:mainnet: Sync Progress: 86.58731497899508<br>
