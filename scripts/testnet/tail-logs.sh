#!/usr/bin/sh

multitail -cT ANSI node_log.txt -cT ANSI db_sync_log.txt

