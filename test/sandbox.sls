sync_extmods:
  module.run:
    - name: saltutil.sync_all

init_repo:
  cmd.script:
    - name: salt://test/initrepo.sh
    - cwd: /tmp/kitchen/srv/salt/test
    - shell: /bin/sh

gitstack_config:
  file.managed:
    - name: /tmp/kitchen/etc/salt/minion.d/gitstack.conf
    - makedirs: true
    - source: salt://test/gitstack.conf
    - template: jinja
