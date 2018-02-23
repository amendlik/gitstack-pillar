#!/usr/bin/env sh
result=pass

$(dirname $0)/../checkpillar.sh 'stacktest' 'True' || result=fail
$(dirname $0)/../checkpillar.sh 'repo_a' 'present' || result=fail
$(dirname $0)/../checkpillar.sh 'repo_b' 'present' || result=fail
$(dirname $0)/../checkpillar.sh 'reponame' 'repo_b' || result=fail

[ $result = fail ] && exit 1
exit 0
