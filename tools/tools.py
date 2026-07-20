"""
Tool registry - built by discovery, not by hand.

Every module in this package is imported and scanned for module-level Tool
instances. Dropping a new `*_tool.py` file into `tools/` registers its tools
automatically: no edit to this file, no import to remember.

A module that fails to import (e.g. an optional dependency is missing) is
logged and skipped - one broken tool must not take the whole assistant down.
"""

import importlib
import logging
import os
import pkgutil

try:
    from .tool import Tool
except ImportError:
    from tool import Tool

logger = logging.getLogger(__name__)

# Modules that are not tool modules:
#   tool      - defines the Tool class itself
#   tools     - this registry
#   file_tool - its tools are per-user, built on demand by make_file_tools(user_id)
SKIP_MODULES = {"tool", "tools", "file_tool"}


def _import_tool_module(module_name):
    """Imports a sibling module, whether `tools` is used as a package or not."""
    if __package__:
        return importlib.import_module(f".{module_name}", __package__)
    return importlib.import_module(module_name)


def discover_tools():
    """Returns every Tool instance defined at module level in this package.

    Duplicates are removed by tool name: a module that re-exports another
    module's tool must not register it twice.
    """
    package_dir = os.path.dirname(os.path.abspath(__file__))
    discovered = {}

    for _finder, module_name, _is_pkg in pkgutil.iter_modules([package_dir]):
        if module_name in SKIP_MODULES:
            continue

        try:
            module = _import_tool_module(module_name)
        except Exception as error:
            logger.error(
                "Skipping tool module '%s' - it failed to import: %s",
                module_name, error,
            )
            continue

        for value in vars(module).values():
            if isinstance(value, Tool) and value.name not in discovered:
                discovered[value.name] = value
                logger.debug(
                    "Discovered tool '%s' in %s.py", value.name, module_name
                )

    logger.info(
        "Discovered %d tools: %s",
        len(discovered), ", ".join(sorted(discovered)),
    )
    return list(discovered.values())


tools = discover_tools()
