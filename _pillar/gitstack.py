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
from salt.utils.data import repack_dictlist
from salt.exceptions import SaltException

PER_REMOTE_OVERRIDES = salt.pillar.git_pillar.PER_REMOTE_OVERRIDES
PER_REMOTE_ONLY = tuple(set(list(salt.pillar.git_pillar.PER_REMOTE_ONLY) + ["stack"]))

# Set up logging
LOG = logging.getLogger(__name__)

# Define the module's virtual name
__virtualname__ = "gitstack"


def __virtual__():
    """
    Only load if GitStack pillars are defined
    """
    gitstack_pillars = [x for x in __opts__["ext_pillar"] if "gitstack" in x]
    if not gitstack_pillars:
        # No GitStack external pillars were configured
        return False

    return __virtualname__


def ext_pillar(minion_id, pillar, *repos, **single_repo_conf):

    try:
        stacks, gitpillar = _init_gitpillar(repos, single_repo_conf)

    except GitStackPillarException as ex:
        LOG.error(ex.message)
        return {}

    # Initialize variables
    stack_config = []
    stack_config_kwargs = {}

    # Replace relative paths with the absolute path of the cloned repository
    if single_repo_conf:
        stack_config = _resolve_stack(
            single_repo_conf["stack"], list(gitpillar.pillar_dirs.items())[0][0]
        )
    else:
        pillar_dirs = list(gitpillar.pillar_dirs.keys())
        for idx, stack in enumerate(stacks):
            try:
                pillar_dir = pillar_dirs[idx]
            except IndexError:
                LOG.warning("Ignoring GitStack stack configuration: %s", stack)
                LOG.warning("Ignoring GitStack repo maybe failed checkout")
                continue

            if isinstance(stack, dict):
                salt.utils.dictupdate.update(
                    stack_config, _resolve_stack(stack, pillar_dir)
                )

            elif isinstance(stack, list):
                stack_config.extend(_resolve_stack(stack, pillar_dir))
            else:
                stack_config.append(_resolve_stack(stack, pillar_dir))

    return _call_stack_pillar(minion_id, pillar, stack_config, stack_config_kwargs)


def _init_gitpillar(repos, single_repo_conf):

    # Retrieve configuration
    if isinstance(repos, (list, tuple)) and len(repos) > 0:
        stacks, init_gitpillar_args = _get_init_args(repos)

    else:
        # Invalid configuration
        raise GitStackPillarException(
            "Configuration for GitStack must be a list of dicts or a single dict"
        )

    opts = copy.deepcopy(__opts__)
    opts["pillar_roots"] = {}
    opts["__git_pillar"] = True

    # check arguments to use with GitPillar, we could check also salt version
    if len(_get_function_varnames(salt.utils.gitfs.GitPillar.__init__)) > 2:
        # Include GLOBAL_ONLY args for Salt versions that require it
        if "global_only" in _get_function_varnames(salt.utils.gitfs.GitPillar.__init__):
            init_gitpillar_args.append(salt.pillar.git_pillar.GLOBAL_ONLY)

        # Initialize GitPillar object
        gitpillar = salt.utils.gitfs.GitPillar(opts, *init_gitpillar_args)

    else:
        # Include GLOBAL_ONLY args for Salt versions that require it
        if "global_only" in _get_function_varnames(
            salt.utils.gitfs.GitPillar.init_remotes
        ):
            init_gitpillar_args.append(salt.pillar.git_pillar.GLOBAL_ONLY)

        # Initialize GitPillar object
        gitpillar = salt.utils.gitfs.GitPillar(opts)
        gitpillar.init_remotes(*init_gitpillar_args)

    if __opts__.get("__role") == "minion":
        # If masterless, fetch the remotes. We'll need to remove this once
        # we make the minion daemon able to run standalone.
        gitpillar.fetch_remotes()
    gitpillar.checkout()

    if not gitpillar.pillar_dirs:
        raise GitStackPillarException(
            "Repositories used by GitStack must be included in the git pillar configuration"
        )

    return stacks, gitpillar


def _get_init_args(repos):
    stacks = []
    invalid_repos_idx = []
    for repo_idx, repo in enumerate(repos):
        keywords = repack_dictlist(repo[next(iter(repo))])
        if "stack" not in keywords:
            # stack param is mandatory in GitStack repos configuration
            LOG.warning(
                "Configuration for GitStack must contain a stack key for each repo."
            )
            LOG.warning(
                "Configured GitStack repo %s (at position %d) will be ignored",
                next(iter(repo)),
                repo_idx,
            )
            invalid_repos_idx.append(repo_idx)
            continue

        stacks.append(keywords["stack"])

    valid_repos = [
        repo for repo_idx, repo in enumerate(repos) if repo_idx not in invalid_repos_idx
    ]
    init_gitpillar_args = [valid_repos, PER_REMOTE_OVERRIDES, PER_REMOTE_ONLY]

    return stacks, init_gitpillar_args


def _resolve_stack(relative, path):
    """
    Resolve relative paths to the absolute path of the cloned Git repo
    """
    if isinstance(relative, dict):
        absolute = {}
        for key, value in relative.items():
            absolute[key] = _resolve_stack(value, path)
    elif isinstance(relative, list):
        absolute = []
        for item in relative:
            absolute.append(_resolve_stack(item, path))
    elif isinstance(relative, str):
        absolute = os.path.join(path, relative)
    else:
        absolute = relative
    return absolute


def _call_stack_pillar(minion_id, pillar, stack_config, stack_config_kwargs):

    # Load the 'stack' pillar module
    stack_pillar = salt.loader.pillars(__opts__, __salt__, __context__)["stack"]

    # Call the 'stack' pillar module
    if isinstance(stack_config, dict):
        return stack_pillar(minion_id, pillar, **stack_config)

    if isinstance(stack_config, list):
        return stack_pillar(minion_id, pillar, *stack_config, **stack_config_kwargs)

    return stack_pillar(minion_id, pillar, stack_config)


def _get_function_varnames(function):
    """
    Return the var names for a function
    """
    return function.__code__.co_varnames


class GitStackPillarException(SaltException):
    """
    Raised when GitStack encounters a problem.
    """
