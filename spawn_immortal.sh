#!/usr/bin/env bash
PORT=$1
while true
do
    python wry.py --port=$PORT --subdomain=static
    sleep 1
done
