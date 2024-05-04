"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         fibonacci = enedis_odoo_bridge.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``fibonacci`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This file can be renamed depending on your needs or safely removed if not needed.

References:
    - https://setuptools.pypa.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""
import os
import sys
import argparse
import logging
import pandas as pd
from datetime import date, datetime
from pathlib import Path

from enedis_odoo_bridge import __version__
from enedis_odoo_bridge.EnedisFluxEngine import EnedisFluxEngine
from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.DataMerger import DataMerger
from enedis_odoo_bridge.processes import UpdateValuesInDraftInvoicesProcess, AddEnedisServiceToDraftInvoiceProcess
from enedis_odoo_bridge.utils import CustomLoggerAdapter, load_prefixed_dotenv, download_new_files_with_progress, recursively_decrypt_zip_files_with_progress

from rich import print, pretty, inspect
from rich.logging import RichHandler
from rich.prompt import Prompt
from rich.console import Console

pretty.install()

__author__ = "Virgile Daugé"
__copyright__ = "Virgile Daugé"
__license__ = "GPL-3.0-only"

_logger = logging.getLogger('enedis_odoo_bridge')
_logger = CustomLoggerAdapter(_logger, {"prefix": ""})


# ---- Python API ----
# The functions defined in this section can be imported by users in their
# Python scripts/interactive interpreter, e.g. via
# `from enedis_odoo_bridge.skeleton import fib`,
# when using this Python module as a library.



# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.

def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Pont entre les données de l'Enedis et Odoo")
    parser.add_argument(
    "command",
    help="The command to execute",
    type=str,
    choices=['facturation', 'services'],  # Example commands
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"enedis_odoo_bridge {__version__}",
    )
    #parser.add_argument(dest="n", help="n-th Fibonacci number", type=int, metavar="INT")
    parser.add_argument('-p', '--data-path',
        dest="data_path",
        default='~/data/flux_enedis',
        help="path to data", 
        type=str,)
    parser.add_argument('-s', '--simulation',
        dest="sim",
        default=False,
        action="store_true",
        help="Perform odoo interactions on '-duplicated' database",)
    parser.add_argument('-u', '--update-flux',
        dest="update_flux",
        default=False,
        action="store_true",
        help="If present, the flux will be updated from ftp",)
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    today = date.today()
    parser.add_argument(
        '-d',
        '--date',
        default=today.isoformat(),
        type=date.fromisoformat,
    )
    return parser.parse_args(args)

def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    #logformat = "[%(asctime)s] %(levelname)s:%(name)s: %(message)s"
    logformat = "[%(asctime)s] %(message)s"
    logging.basicConfig(
        level=loglevel, #stream=sys.stdout, 
        format=logformat, datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[RichHandler(rich_tracebacks=True)]
    )

def main(args):
    """Wrapper allowing :func:`fib` to be called with string arguments in a CLI fashion

    Instead of returning the value from :func:`fib`, it prints the result to the
    ``stdout`` in a nicely formatted message.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    console = Console(markup=True, highlight=True)
    logger = CustomLoggerAdapter(_logger, {"prefix": ""})
    setup_logging(args.loglevel)

    env = load_prefixed_dotenv(prefix='ENEDIS_ODOO_BRIDGE_')
    data_path = Path(args.data_path).expanduser()


    if args.update_flux:
        print(f"Fetching new files from {env['FTP_ADDRESS']} ftp...")
        files = download_new_files_with_progress(config=env, local=data_path, tasks=['R15', 'F15'])
        decrypted_files = recursively_decrypt_zip_files_with_progress(directory=data_path, 
                                                                      key=bytes.fromhex(env['AES_KEY']),
                                                                      iv=bytes.fromhex(env['AES_IV']),
                                                                      prefix='decrypted_')
    
    enedis = EnedisFluxEngine(config=env, path=data_path, flux=['R15', 'F15'], logger=logger)

    if args.command == 'facturation':
        process = UpdateValuesInDraftInvoicesProcess(config=env,
                    date=args.date,
                    enedis=enedis,
                    odoo=OdooAPI(config=env, sim=args.sim, logger=logger), 
                    logger=logger)

    elif args.command =='services':
        process = AddEnedisServiceToDraftInvoiceProcess(config=env,
                    date=args.date,
                    enedis=enedis,
                    odoo=OdooAPI(config=env, sim=args.sim, logger=logger), 
                    logger=logger)
        
    if not args.sim and process.will_update_production_db:
        confirm = Prompt.ask(f"This will update [red]{env['DB']}[/red] Odoo Database from [red]{env['URL']}[/red], are you sure you want to continue?", 
                                 choices=["y", "n"], default="n", console=console)
        if confirm.lower()!= 'y':
            console.print("└──Operation cancelled")
            exit(0)
    process.run()

def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m enedis_odoo_bridge.skeleton 42
    #
    run()
