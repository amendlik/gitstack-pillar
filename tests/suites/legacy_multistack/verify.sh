#!/usr/bin/env sh
result=pass

echo 'Testing Salt version' $(sudo salt-call -c /tmp/kitchen/etc/salt --local --output newline_values_only grains.get saltversion) '(legacy multistack suite)'

$(dirname $0)/../checkpillar.sh 'stacktest' 'True' || result=fail
$(dirname $0)/../checkpillar.sh 'test2' 'present' || result=fail

[ $result = fail ] && exit 1
exit 0

