# GitStack Pillar

A SaltStack Pillar that enables all the great features of the [Stack Pillar](https://docs.saltstack.com/en/latest/ref/pillar/all/salt.pillar.stack.html#module-salt.pillar.stack), but using a Git repository for backend file storage.

## Getting Started

### Prerequisites

A supported Python interface to Git must be installed. For Salt releases earlier than 2015.8.0, GitPython is the only supported provider. Beginning with Salt version 2015.8.0, pygit2 is now supported in addition to GitPython.

### Installing

If the gitfs fileserver backend is enabled, this repository can be added as a remote repository.

In the Salt Master configuration, add the following lines:
```
fileserver_backend:
  - git

gitfs_remotes:
  - https://github.com/amendlik/gitstack-pillar.git
```

If the gitfs fileserver backend is not enabled, simply download the file to the `_pillar` directory in the fileserver root directory.
```
mkdir -p /srv/salt/_pillar
cd /srv/salt/_pillar
curl -O https://raw.githubusercontent.com/amendlik/gitstack-pillar/master/_pillar/gitstack.py
```

Regardless of which approach above was followed, one additional step is required to make the module available to the Salt Master. Run the following command on the Salt Master:
```
salt-run saltutil.sync_pillar
```

### Configuration

The GitStack Pillar requires the same configuration as would be provided to the Stack Pillar, with a few differences. For a detailed explanation of these configuration options, see the [Stack Pillar documentation](https://docs.saltstack.com/en/latest/ref/pillar/all/salt.pillar.stack.html#module-salt.pillar.stack).

The differences required for GitStack vs. Stack configuration are these:

1. The key under `ext_pillar` must be `gitstack`, rather than `stack`
2. Keys for `repo` and `branch` must be included under the `gitstack` key. These specify the Git repository and branch that contain the stack configuration files.
3. The `stack` key (which would be directly beneath `ext_pillar` when using the Stack Pillar), must be nested under the `gitstack` key.
4. Configuration file paths must be relative to the root of the Git repository.
5. Any Git repository referenced in the GitStack configuration must also be referenced in the Git Pillar configuration.

#### Example 1
Here is a simple example of a Stack Pillar configuration, which depends on files from the local filesystem:
```
ext_pillar:
  - stack: /path/to/stack.cfg
```
The equivalent GitStack Pillar configuration, fetching files from a remote Git repository, might look like this:
```
ext_pillar:
  - gitstack:
      stack: _stack/stack.cfg
      repo: https://github.com/org/myrepo.git
      branch: master
  - git:
    - master https://github.com/org/myrepo.git
```

#### Example 2
Here is an example of a Stack Pillar configuration, which depends on files from the local filesystem:
```
ext_pillar:
  - stack:
      pillar:environment:
        dev: /path/to/dev/stack.cfg
        prod: /path/to/prod/stack.cfg
      grains:custom:grain:
        value:
          - /path/to/stack1.cfg
          - /path/to/stack2.cfg
      opts:custom:opt:
        value: /path/to/stack0.cfg
```
The equivalent GitStack Pillar configuration, fetching files from a remote Git repository, might look like this:
```
ext_pillar:
  - gitstack:
      stack:
        pillar:environment:
          dev: _stack/stack.cfg
          prod: _stack/stack.cfg
        grains:custom:grain:
          value:
            - _stack/stack1.cfg
            - _stack/stack2.cfg
        opts:custom:opt:
          value: _stack/stack0.cfg
      repo: https://github.com/org/myrepo.git
      branch: master
  - git:
    - master https://github.com/org/myrepo.git
```

#### Example 3
Here is an example of Git Pillar configuration
```
ext_pillar:
  - git:
    - master https://mydomain.tld/foo.git:
      - root: pillar
    - master https://mydomain.tld/baz.git
    - dev https://mydomain.tld/qux.git
```
The equivalent GitStack Pillar configuration, fetching files from several remotes Git repository, assuming we have a stack config under each repositories,
might look like this:
```
ext_pillar:
  - gitstack:
    - master https://mydomain.tld/foo.git:
      - root: pillar
      - stack: _stack/stack_foo.cfg
    - master https://mydomain.tld/baz.git:
      - stack: _stack/stack_baz.cfg
    - dev https://mydomain.tld/qux.git:
      - stack: _stack/stack_qux.cfg

  - git:
    - master https://mydomain.tld/foo.git:
      - root: pillar
    - master https://mydomain.tld/baz.git
    - dev https://mydomain.tld/qux.git
```
the Stack Pillar configurations are managed as they were:
```
ext_pillar:
  - stack:
    - /path/to/stack_foo.cfg
    - /path/to/stack_baz.cfg
    - /path/to/stack_qux.cfg
```
in this scenario is very important consider the repositeries layout and in case manage conflicts using the `mountpoint` parameter as for Git Pillar configuration.

#### Explanation
1. The entire Stack Pillar configuration is nested under the `stack` key, which is inself nested under the `gitstack` key. This configuration will be modified to resolve the relative file paths to the absolute path of the local cache of the Git repository, then passed to the Stack Pillar.

2. The configuration file paths are relative paths to the root of the Git repository. In the examples above, they are located within a `_stack` directory at the repository root. This is not strictly necessary - the files cloud be in any directory, or stored at the root. Since the cloned repository will share a namespace with the Git Pillar, keeping the stack files in a seperate directory helps avoid confusion and name conflicts.

3. Under the `gitstack` key, the `repo` and `branch` keys specify which remote repository to clone, and which branch should be checked out. The `branch` keyword will take a default value of `master` if omitted.

4. The remote repository is also defined as a `git` external pillar. This is necessary for the remote repository to be polled for changes. The Salt Master runs an internal maintenance routine that specifically looks for repositories configured for the Git Pillar and fetches changes from those repositories. The only way to take advantage of that service is to configure the repository as a Git Pillar repository. As long as the Pillar Top File does not include GitStack files, there will be no conflict. It is also possible to include files for both the Git Pillar and GitStack pillar in the same Git repository, hence the recommendation to use a separate `_stack` directory above.

## Internals

The GitStack pillar relies heavily on code already present in the SaltStack code base, specifically the Stack Pillar module. Here is a brief description of how it works:

1. A maintenance routine runs every minute within the Salt Master. Among other things, it looks for a Git external pillar configuration and fetches changes to those defined remote repository.

2. GitStack depends on that maintenance routine to fetch changes to its configured remote repositorie, which is why repositories must also be configured under the Git Pillar. GitStack checks out the requested branch and stores the absolute path to the Git working directory on the local system.

3. GitStack then recursively walks through the value of the `stack` key and replaces relative file paths with absolute paths by prepending the Git working directory.

4. The entire Stack configuration (with absolute paths) is then passed to the Stack Pillar for processing.

5. All processing of configuration files, YAML files, Jinja templates, etc. is handled by the Stack Pillar.

## License

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

## Acknowledgments
* Bruno Binet [@bbinet](https://github.com/bbinet) - original author of the Stack Pillar
