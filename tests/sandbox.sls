init_repo:
  cmd.script:
    - name: salt://tests/initrepo.sh
    - cwd: {{ pillar['kitchen']['provisioner']['root_path'] }}/srv/salt/tests
    - shell: /bin/sh

gitstack_config:
  file.managed:
    - name: {{ pillar['kitchen']['provisioner']['root_path'] }}/etc/salt/minion.d/gitstack.conf
    - makedirs: true
    - source: salt://tests/gitstack.conf
    - template: jinja
