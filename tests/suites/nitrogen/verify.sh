#!/usr/bin/env sh
set -x
if [ $(sudo salt-call -c /tmp/kitchen/etc/salt --local --output newline_values_only pillar.get stacktest) != "True" ]; then
  exit 1
fi

exit 0
