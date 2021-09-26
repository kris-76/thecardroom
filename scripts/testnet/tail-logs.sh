#!/usr/bin/sh

multitail -cT ANSI node_log.txt -cT ANSI dbsync_log.txt
