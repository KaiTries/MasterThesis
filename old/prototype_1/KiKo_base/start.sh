#!/usr/bin/env bash
set -euo pipefail

# python traditional-packer.py &
python seller.py &
PACKER=$!

sleep 1

python buyer.py &
WRAPPER=$!


read -n1 -rsp $'Press any key to stop...\n'

kill $PACKER $WRAPPER 



