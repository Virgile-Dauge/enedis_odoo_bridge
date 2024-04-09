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

import argparse
import logging
import sys
import pandas as pd
from datetime import date
from calendar import monthrange

from enedis_odoo_bridge import __version__
from R15Parser import R15Parser
from OdooAPI import OdooAPI
from Turpe import Turpe

from rich import print, pretty, inspect
from rich.logging import RichHandler

pretty.install()

__author__ = "Virgile Daugé"
__copyright__ = "Virgile Daugé"
__license__ = "GPL-3.0-only"

_logger = logging.getLogger(__name__)



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
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version=f"enedis_odoo_bridge {__version__}",
    )
    #parser.add_argument(dest="n", help="n-th Fibonacci number", type=int, metavar="INT")
    parser.add_argument(dest="zp", help="zipfile path", type=str, metavar="STR")
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
    parser.add_argument(
        '-d',
        '--date',
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
    setup_logging(args.loglevel)
    _logger.debug("Starting crazy calculations...")
    
    # Gestion des dates
    if not args.date:
        args.date = date.today()
        # On cherche le mois précédent
        if args.date.month == 1:
            args.date = args.date.replace(month=12, year=args.date.year-1)
        else:
            args.date = args.date.replace(month=args.date.month-1)
    starting_date = args.date.replace(day=1)
    ending_date = args.date.replace(day = monthrange(args.date.year, args.date.month)[1])

    r15 = R15Parser(args.zp)
    #print(r15.name)
    #print(r15.to_x_log_enedis())
    
    r15.to_csv()

    releves = r15.data
    
    turpe = Turpe()
    odoo = OdooAPI()
    #inspect(odoo, methods=True)
    # TODO Inject releves in Odoo and get IDS
    #odoo.write_releves(releves)

    drafts = odoo.drafts
    drafts_df = pd.DataFrame(drafts)
    drafts_df.to_csv(r15.working_dir.joinpath('drafts.csv'))

    pdls = [d['pdl'] for d in drafts]
    log_id = odoo.write('x_log_enedis', r15.to_x_log_enedis())[0]
    print(log_id)
    consos = releves[releves['traitable_automatiquement'] == True].set_index(['pdl'])

    # On ajoute "puissance_souscrite" aux consos.
    merged = pd.merge(drafts_df, consos, on='pdl')
    merged.to_csv(r15.working_dir.joinpath('merged.csv'))

    complete = turpe.compute(merged).set_index(['pdl'])
    print(complete)
    lines = pd.DataFrame(odoo.get_lines()).set_index(['pdl'])

    # TODO Verif si pas deux valeurs de PDL identiques
    pas_de_conso = [d['id'] for d in drafts if d['pdl'] not in complete.index or (d['pdl'] in complete.index.values
                                                and not complete.at[d["pdl"], 'traitable_automatiquement'])]
    _logger.warning(f'Pas de consommation pour les factures #{pas_de_conso}')

    lines_to_inject = []
    invoices_to_inject = []
    for d in drafts:
        if d['pdl'] not in complete.index or (d['pdl'] in complete.index.values
                                                and not complete.at[d["pdl"], 'traitable_automatiquement']):
            #_logger.warning(f'Pas de consommation pour {d["pdl"]}')
            #pas_de_conso += [d['pdl']]
            continue
        
        invoices_to_inject = [{'id': d['id'], 'x_log_id': log_id, 'x_turpe' : 9999}]
        _logger.info(f'Consommation pour {d["pdl"]} : {complete.loc[d["pdl"], :]}')
        # TODO Inject lines in Odoo
        to_update = lines.loc[d["pdl"]].set_index(['code'])
        print(to_update)
        # On enlève les dates de la ligne
        abo = to_update.loc['ABO', :]
        lines_to_inject += [{'id': abo['id'], 'name': abo['name'].split('-')[0], 'deferred_start_date': str(starting_date), 'deferred_end_date': str(ending_date)}]
        lines_to_inject += [{'id': to_update.at[False, 'id'], 'name': f"Dont {complete.at[d['pdl'],'turpe']} de taxes d'acheminement"}]

        if 'BASE' in to_update.index:
            lines_to_inject += [{'id': to_update.at['BASE', 'id'], 'quantity': sum(complete.loc[d["pdl"], ['HPH_conso', 'HCH_conso', 'HPB_conso', 'HCB_conso']])}]

        elif 'HP' in to_update.index and 'HC' in to_update.index:
            lines_to_inject += [{'id': to_update.at['HP', 'id'], 'quantity': sum(complete.loc[d["pdl"], ['HPH_conso', 'HPB_conso']])}]
            lines_to_inject += [{'id': to_update.at['HC', 'id'], 'quantity': sum(complete.loc[d["pdl"], ['HCH_conso', 'HCB_conso']])}]

    print(lines_to_inject)
    odoo.update('account.move', invoices_to_inject)
    odoo.update('account.move.line', lines_to_inject)     
    _logger.info("Script ends here")


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
