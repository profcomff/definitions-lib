import os
from typing import Any, Optional, Sequence

from alembic.config import CommandLine, Config


def get_template_directory(self):
    """Return the directory where Alembic setup templates are found.

    This method is used by the alembic ``init`` and ``list_templates``
    commands.

    """
    import definitions

    package_dir = os.path.abspath(os.path.dirname(definitions.__file__))
    return os.path.join(package_dir, "templates")


def main(
    argv: Optional[Sequence[str]] = None,
    prog: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """The console runner function for Defintions."""
    command_line = CommandLine(prog=prog)
    options = command_line.parser.parse_args(argv)
    options.template = "definitions"
    if not hasattr(options, "cmd"):
        # see http://bugs.python.org/issue9253, argparse
        # behavior changed incompatibly in py3.3
        command_line.parser.error("too few arguments")
    Config.get_template_directory = get_template_directory  # type: ignore
    if options.config is None:
        if os.path.isfile("alembic.ini"):
            options.config = "alembic.ini"
        else:
            raise EnvironmentError(
                "File alembic.ini does not exist and was not provided in command line. See --help."
            )

    config = Config(
        file_=options.config,
        ini_section=options.name,
        cmd_opts=options,
    )
    command_line.run_cmd(config, options)


if __name__ == "__main__":
    main()
