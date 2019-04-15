from __future__ import absolute_import

# Import python libs
import copy
import logging
import os

# Import salt libs
import salt.loader
import salt.utils
import salt.utils.gitfs
import salt.utils.dictupdate
import salt.pillar.git_pillar

# Import third party libs
import salt.ext.six as six

try:
    from salt.utils.data import repack_dictlist
except ImportError:
    from salt.utils import repack_dictlist

PER_REMOTE_OVERRIDES = salt.pillar.git_pillar.PER_REMOTE_OVERRIDES
PER_REMOTE_ONLY = tuple(set(list(salt.pillar.git_pillar.PER_REMOTE_ONLY) + ['stack']))

# Set up logging
log = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = 'gitstack'


def __virtual__():
    '''
    Only load if gitstack pillars are defined
    '''
    gitstack_pillars = [x for x in __opts__['ext_pillar'] if 'gitstack' in x]
    if not gitstack_pillars:
        # No gitstack external pillars were configured
        return False

    return __virtualname__


def ext_pillar(minion_id, pillar, *repos, **single_repo_conf):

    # Checkout the ext_pillar sources
    opts = copy.deepcopy(__opts__)
    opts['pillar_roots'] = {}
    opts['__git_pillar'] = True
    stacks = []
    invalid_repos_idx = []

    ## legacy configuration with a plain dict under gitstack ext_pillar key
    if single_repo_conf and single_repo_conf.get('repo', None) is not None:
        branch = single_repo_conf.get('branch', 'master')
        repo = single_repo_conf['repo']
        remote = ' '.join([branch, repo])
        init_gitpillar_args = [ [remote], PER_REMOTE_OVERRIDES, PER_REMOTE_ONLY ]
        if 'stack' not in single_repo_conf:
            log.error('A stack key is mandatory in gitstack configuration')
            return {}

    ## new configuration way
    elif isinstance(repos, (list, tuple)) and len(repos) > 0:
        for repo_idx, repo in enumerate(repos):
            kw = repack_dictlist(repo[next(iter(repo))])
            if 'stack' not in kw:
                # stack param is mandatory in gitstack repos configuration
                log.warning('Configuration for gitstack must contain a stack key for each repo.')
                log.warning('Configured gitstack repo %s (at position %d) will be ignored' % (next(iter(repo)), repo_idx))
                invalid_repos_idx.append(repo_idx)
                continue

            stacks.append(kw['stack'])

        valid_repos = [repo for repo_idx, repo in enumerate(repos) if repo_idx not in invalid_repos_idx]
        init_gitpillar_args = [ valid_repos, PER_REMOTE_OVERRIDES, PER_REMOTE_ONLY ]

    else:
        ### Invalid configuration
        log.error('Configuration for gitstack must be a list of dicts or a single dict')
        return {}

    # check arguments to use with GitPillar, we could check also salt version
    if len(_get_function_varnames(salt.utils.gitfs.GitPillar.__init__)) > 2:
        # Include GLOBAL_ONLY args for Salt versions that require it
        if 'global_only' in salt.utils.gitfs.GitPillar.__init__.im_func.func_code.co_varnames:
            init_gitpillar_args.append(salt.pillar.git_pillar.GLOBAL_ONLY)

        # Initialize GitPillar object
        gitpillar = salt.utils.gitfs.GitPillar(opts, *init_gitpillar_args)

    else:
        # Include GLOBAL_ONLY args for Salt versions that require it
        if 'global_only' in salt.utils.gitfs.GitPillar.init_remotes.im_func.func_code.co_varnames:
            init_gitpillar_args.append(salt.pillar.git_pillar.GLOBAL_ONLY)

        # Initialize GitPillar object
        gitpillar = salt.utils.gitfs.GitPillar(opts)
        gitpillar.init_remotes(*init_gitpillar_args)


    if __opts__.get('__role') == 'minion':
        # If masterless, fetch the remotes. We'll need to remove this once
        # we make the minion daemon able to run standalone.
        gitpillar.fetch_remotes()
    gitpillar.checkout()

    # Prepend the local path of the cloned Git repo
    if not gitpillar.pillar_dirs:
        log.error('Repositories used by gitstack must be included in the git pillar configuration')
        return {}

    # Initialize variables
    stack_config = []
    stack_config_kwargs = {}

    # Replace relative paths with the absolute path of the cloned repository
    if single_repo_conf:
        stack_config = _resolve_stack(single_repo_conf['stack'], list(gitpillar.pillar_dirs.items())[0][0])
    else:
        pillar_dirs = list(gitpillar.pillar_dirs.keys())
        for idx, stack in enumerate(stacks):
            try:
                pillar_dir = pillar_dirs[idx]
            except IndexError:
                log.warning('Ignoring gitstack stack configuration: %s' % stack)
                log.warning('Ignoring gitstack repo maybe failed checkout')
                continue

            if isinstance(stack, dict):
                # TODO: use salt.utils.dictupdate.merge
                stack_config_kwargs.update(_resolve_stack(stack, pillar_dir))
            elif isinstance(stack, list):
                stack_config.extend(_resolve_stack(stack, pillar_dir))
            else:
                stack_config.append(_resolve_stack(stack, pillar_dir))

    # Load the 'stack' pillar module
    stack_pillar = salt.loader.pillars(__opts__, __salt__, __context__)['stack']

    # Call the 'stack' pillar module
    if isinstance(stack_config, dict):
        return stack_pillar(minion_id, pillar, **stack_config)

    elif isinstance(stack_config, list):
        return stack_pillar(minion_id, pillar, *stack_config, **stack_config_kwargs)

    else:
        return stack_pillar(minion_id, pillar, stack_config)


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


def _get_function_varnames(fn):
    '''
    Return the var names for a function
    '''
    if six.PY2:
        return fn.im_func.func_code.co_varnames
    return fn.__code__.co_varnames
