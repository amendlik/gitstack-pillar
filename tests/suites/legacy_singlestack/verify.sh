#!/usr/bin/env sh
result=pass

echo 'Testing Salt version' $(sudo salt-call -c /tmp/kitchen/etc/salt --local --output newline_values_only grains.get saltversion) '(legacy singlestack suite)'

$(dirname $0)/../checkpillar.sh 'stacktest' 'True' || result=fail

[ $result = fail ] && exit 1
exit 0

