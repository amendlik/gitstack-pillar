#!/usr/bin/env sh
result=pass

echo 'Testing Salt version' $(sudo salt-call -c /tmp/kitchen/etc/salt --local --output newline_values_only grains.get saltversion)

$(dirname $0)/../checkpillar.sh 'stacktest' 'True' || result=fail
$(dirname $0)/../checkpillar.sh 'repo_a' 'present' || result=fail
$(dirname $0)/../checkpillar.sh 'repo_b1' 'present' || result=fail
$(dirname $0)/../checkpillar.sh 'repo_b2' 'present' || result=fail
$(dirname $0)/../checkpillar.sh 'reponame' 'repo_b2' || result=fail
$(dirname $0)/../checkpillar.sh 'template_key' 'test_value' || result=fail
$(dirname $0)/../checkpillar.sh 'test2' 'present' || result=fail

[ $result = fail ] && exit 1
exit 0
