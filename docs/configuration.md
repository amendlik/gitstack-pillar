# GitStack Configuration
The GitStack Pillar requires the same configuration as would be provided to the Stack Pillar, with a few differences.

For a detailed explanation of all the configuration options available in the Stack Pillar, see the [Stack Pillar documentation](https://docs.saltstack.com/en/latest/ref/pillar/all/salt.pillar.stack.html#module-salt.pillar.stack).

The differences required for GitStack vs. Stack configuration are these:

1. The key under `ext_pillar` must be `gitstack`, rather than `stack`
2. Keys for `repo` and `branch` must be included under the `gitstack` key. These specify the Git repository and branch that contain the stack configuration files.
3. The `stack` key (which would be directly beneath `ext_pillar` when using the Stack Pillar), must be nested under the `gitstack` key.
4. Configuration file paths must be relative to the root of the Git repository.
5. Any Git repository referenced in the GitStack configuration must also be referenced in the Git Pillar configuration.

#### Note:
Users of Salt Carbon (2016.11) and earlier should refer to the [legacy configuration documentation](docs/carbon_config.md).
The documentation below is for users of Salt Nitrogen (2017.7), which supports multiple Git repositories.

## Configuration Examples

### Example 1
Here is a simple example of a Stack Pillar configuration, which depends on files from the local filesystem:
```
ext_pillar:
  - stack: /path/to/stack.cfg
```
The equivalent GitStack Pillar configuration, fetching files from a remote Git repository, would look like this:
```
ext_pillar:
  - gitstack:
    - master https://github.com/org/myrepo.git:
      - stack: _stack/stack.cfg
  - git:
    - master https://github.com/org/myrepo.git
```

### Example 2
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
The equivalent GitStack Pillar configuration, fetching files from a remote Git repository, would look like this:
```
ext_pillar:
  - gitstack: 
    - master https://github.com/org/myrepo.git:
      - stack:
          pillar:environment:
            dev: _stack/stack.cfg
            prod: _stack/stack.cfg
          grains:custom:grain:
            value:
              - _stack/stack1.cfg
              - _stack/stack2.cfg
          opts:custom:opt:
            value: _stack/stack0.cfg
  - git: 
    - master https://github.com/org/myrepo.git
```

### Example 3
It is also possible to configure GitStack using multiple Git repositories:
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
## Explanation
1. The entire Stack Pillar configuration is nested under the `stack` key, which is inself nested under the `gitstack` key. This configuration will be modified to resolve the relative file paths to the absolute path of the local cache of the Git repository, then passed to the Stack Pillar.

2. The configuration file paths are relative paths to the root of the Git repository. In the examples above, they are located within a `_stack` directory at the repository root. This is not strictly necessary - the files cloud be in any directory, or stored at the root. Since the cloned repository will share a namespace with the Git Pillar, keeping the stack files in a seperate directory helps avoid confusion and name conflicts.

3. Under the `gitstack` key, the `repo` and `branch` keys specify which remote repository to clone, and which branch should be checked out. The `branch` keyword will take a default value of `master` if omitted.

4. The remote repository is also defined as a `git` external pillar. This is necessary for the remote repository to be polled for changes. The Salt Master runs an internal maintenance routine that specifically looks for repositories configured for the Git Pillar and fetches changes from those repositories. The only way to take advantage of that service is to configure the repository as a Git Pillar repository. As long as the Pillar Top File does not include GitStack files, there will be no conflict. It is also possible to include files for both the Git Pillar and GitStack pillar in the same Git repository, hence the recommendation to use a separate `_stack` directory above.
