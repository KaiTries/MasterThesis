#!/usr/bin/env bash

# start environment
cd env

cd protocols
python protocol.py &
PROTOCOL=$!

cd ..

java -jar yggdrasil-0.0.0-SNAPSHOT-all.jar -conf conf/buy_demo.json &
ENV=$! 

sleep 5

cd ..

python -m agents.bazaar.bazaar_agent &
BAZAAR_AGENT=$!


# stop everything
sleep 5
read -n1 -rsp $'Press any key to stop...\n'
kill $ENV
kill $BAZAAR_AGENT
kill $PROTOCOL