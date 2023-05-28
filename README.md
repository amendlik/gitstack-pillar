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

## Configuration
For details on configuring the GitStack pillar, see the [configuration documentation](docs/configuration.md).

## Internals

The GitStack pillar relies heavily on code already present in the SaltStack code base, specifically the Stack Pillar module. Here is a brief description of how it works:

1. A maintenance routine runs every minute within the Salt Master. Among other things, it looks for a Git external pillar configuration and fetches changes to those defined remote repositories.

2. GitStack depends on that maintenance routine to fetch changes to its configured remote repositories, which is why repositories must also be configured under the Git Pillar. GitStack checks out the requested branch and stores the absolute path to the Git working directory on the local system.

3. GitStack then recursively walks through the value of the `stack` key and replaces relative file paths with absolute paths by prepending the Git working directory.

4. The entire Stack configuration (with absolute paths) is then passed to the Stack Pillar for processing.

5. All processing of configuration files, YAML files, Jinja templates, etc. is handled by the Stack Pillar.

## Running Tests
Set up test environment
```
$ gem install bundle
$ bundle install
```
Test everything:
```
$ DOCKER_BUILDKIT=0 bundle exec kitchen test
```

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
