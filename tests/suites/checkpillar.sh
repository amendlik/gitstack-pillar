key=$1
expected=$2

actual=$(sudo salt-call -c /tmp/kitchen/etc/salt --local --output newline_values_only pillar.get $key XUNDEFINEDX)
rc=$?

if [ $rc -ne 0 ]; then
  echo "salt-call command failed with rc=$rc"
  exit $rc
fi

if [ "$actual" = "XUNDEFINEDX" ]; then
  echo "test FAILED: pillar key '$key' is not defined"
  exit 1
fi

if [ "$actual" != "$expected" ]; then
  echo "test FAILED: '$actual' does not match expected value: '$expected'"
  exit 1
fi

echo "test PASSED: $key = $actual"
exit 0
