from __future__ import absolute_import

# Import python libs
import copy
import logging
import os

# Import salt libs
import salt.utils
import salt.utils.gitfs
import salt.utils.dictupdate
import salt.pillar.stack
import salt.pillar.git_pillar

# Import modules required by stack pillar
import posixpath
from functools import partial
from glob import glob
import yaml
from jinja2 import FileSystemLoader, Environment

# Import third party libs
import salt.ext.six as six

# Set up logging
log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'gitstack'

# Copy stack global objects into this namespace
stack_ext_pillar = salt.utils.namespaced_function(salt.pillar.stack.ext_pillar, globals())
_to_unix_slashes = salt.utils.namespaced_function(salt.pillar.stack._to_unix_slashes, globals())
_construct_unicode = salt.utils.namespaced_function(salt.pillar.stack._construct_unicode, globals())
_process_stack_cfg = salt.utils.namespaced_function(salt.pillar.stack._process_stack_cfg, globals())
_cleanup = salt.utils.namespaced_function(salt.pillar.stack._cleanup, globals())
_merge_dict = salt.utils.namespaced_function(salt.pillar.stack._merge_dict, globals())
_merge_list = salt.utils.namespaced_function(salt.pillar.stack._merge_list, globals())
_parse_stack_cfg = salt.utils.namespaced_function(salt.pillar.stack._parse_stack_cfg, globals())
strategies = salt.pillar.stack.strategies


def __virtual__():
    '''
    Only load if gitstack pillars are defined
    '''
    gitstack_pillars = [x for x in __opts__['ext_pillar'] if 'gitstack' in x]
    if not gitstack_pillars:
        # No gitstack external pillars were configured
        return False

    return __virtualname__


def ext_pillar(minion_id, pillar, *args, **kwargs):

    # Checkout the ext_pillar sources
    opts = copy.deepcopy(__opts__)
    opts['pillar_roots'] = {}
    opts['__git_pillar'] = True
    gitpillar = salt.utils.gitfs.GitPillar(opts)

    gitpillar.init_remotes([' '.join([kwargs.get('branch', 'master'), kwargs['repo']])],
                           salt.pillar.git_pillar.PER_REMOTE_OVERRIDES, salt.pillar.git_pillar.PER_REMOTE_ONLY)
    if __opts__.get('__role') == 'minion':
        # If masterless, fetch the remotes. We'll need to remove this once
        # we make the minion daemon able to run standalone.
        gitpillar.fetch_remotes()
    gitpillar.checkout()

    # Prepend the local path of the cloned Git repo
    if not gitpillar.pillar_dirs:
        log.error('Repositories used by gitstack must be included in the git pillar configuration')
        return {}

    stack = _resolve_stack(kwargs['stack'], list(gitpillar.pillar_dirs.items())[0][0])

    # Call the stack pillar module
    if isinstance(stack, dict):
        return stack_ext_pillar(minion_id, pillar, **stack)

    elif isinstance(stack, list):
        return stack_ext_pillar(minion_id, pillar, *stack)

    else:
        return stack_ext_pillar(minion_id, pillar, stack)


def _resolve_stack(x, path):
    '''
    Resolve relative paths to the absolute path of the cloned Git repo
    '''
    if isinstance(x, dict):
        y = {}
        for key, value in six.iteritems(x):
            y[key] = _resolve_stack(value, path)
    elif isinstance(x, list):
        y = []
        for item in x:
            y.append(_resolve_stack(item, path))
    elif isinstance(x, six.string_types):
        y = os.path.join(path, x)
    else:
        y = x
    return y
