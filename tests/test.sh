#!/bin/bash

if [ $# -gt 0 ]
then
    target="$1"
else
    target="http://127.0.0.1:5000"
fi

function run() {
    address=$1
    keyword=$2
    echo "Testing grepping $keyword on page $address" 
    wget -O - $target/$address 2>/dev/null | grep -F "$keyword" >/dev/null
    if [ $? -ne 0 ]
    then
        echo "*** Test failed: grep $keyword on page $address"
    fi
}

echo "Running tests on $target"
run "" "Welcome"
run "latest0th" "?level=" # table is not empty
run "stats" "Date.UTC"
run "stats" "johnny_faneca"
run "stats" "?level="
run "player?pseudo=zapkt" "before January 20, 2006"
run "player?pseudo=zapkt" "<b>61</b>"
run "player?pseudo=zapkt" "<b>588</b>"
run "player?pseudo=slkdjf" "Player not found"
run "all_scores?level=00-0" "demo?player="
run "all_scores?level=toto" "invalid level id"
run "all_scores?level=100-4" "invalid level id"
run "all_scores?level=-1" "invalid level id"
run "all_scores?level=88-6" "invalid level id"
run "level?level=00-0" "trib4lmaniac"
run "level?level=00-0&avg=1" "trib4lmaniac"
run "level?level=00-0&top=5" "trib4lmaniac"
run "level?level=00-0&by_place=1" "250.875"
run "level?level=00-0&diff=1" "1.175"
run "demo?player=EddyMataGallos&level_id=884&timestamp=2012-12-31%2016:48:22" "1450:35791394"
