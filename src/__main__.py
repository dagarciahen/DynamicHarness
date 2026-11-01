"""DynamicHarness command-line composition root."""

from __future__ import annotations

import os
from pathlib import Path

import click
from dynamicharness.app.cli import create, run
from dynamicharness.execution.cli import (
    clean_runtime_command,
    clean_tasks,
    list_tasks,
)

_MAIN_EPILOG = """\
\b
Examples:
  loom run applications/<app>/workflows/<agent>.yaml
  loom create applications/<app>/workflows/<agent>.yaml
  loom create applications/<app>/workflows/<agent>.yaml -o my_app.py

Use 'loom <command> -h' for more details on each command.
"""


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog=_MAIN_EPILOG,
)
@click.pass_context
def main(context: click.Context) -> None:
    """DynamicHarness - AI agent harness CLI."""

    try:
        from dynamicharness.config import C

        agent_root = Path(C.agent_root).resolve()
        if Path.cwd().resolve() != agent_root:
            os.chdir(agent_root)
    except Exception:
        pass


for command in (
    run,
    create,
    list_tasks,
    clean_tasks,
    clean_runtime_command,
):
    main.add_command(command)


if __name__ == "__main__":
    main()
