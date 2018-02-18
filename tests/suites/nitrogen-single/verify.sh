#!/usr/bin/env sh
result=pass

$(dirname $0)/../checkpillar.sh 'stacktest' 'True' || result=fail

[ $result = fail ] && exit 1
exit 0
