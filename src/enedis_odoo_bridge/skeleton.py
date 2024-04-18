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
from dotenv import load_dotenv

from enedis_odoo_bridge import __version__
from enedis_odoo_bridge.EnedisFluxEngine import EnedisFluxEngine
from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.DataMerger import DataMerger
from enedis_odoo_bridge.Turpe import Turpe
from enedis_odoo_bridge.utils import gen_dates, load_prefixed_dotenv

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
    parser.add_argument('-z', '--zip-path',
        dest="zp", 
        help="zipfile path", 
        type=str, 
        metavar="STR")
    parser.add_argument('-s', '--simulation',
        dest="sim",
        default=False,
        action="store_true",
        help="Perform odoo interactions on '-duplicated' database",)
    parser.add_argument('-e', '--enedis-engine',
        dest="enedis_engine",
        default=False,
        action="store_true",
        help="Enedis Flux engine",)
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
    setup_logging(args.loglevel)
    env = load_prefixed_dotenv(prefix='ENEDIS_ODOO_BRIDGE_')

    if args.enedis_engine:
        _logger.debug("Starting Enedis engine...")
        enedis = EnedisFluxEngine(config=env, path='~/data/flux_enedis', flux=['R15'], update=args.update_flux)
        #estimates = enedis.estimate_consumption(start=starting_date, end=ending_date)
        #_logger.debug(f"{estimates}")
        exit()

    dm = DataMerger(config=env,
                    date=args.date,
                    enedis=EnedisFluxEngine(config=env, 
                                            path='~/data/flux_enedis', 
                                            flux=['R15'], 
                                            update=args.update_flux),
                    odoo=OdooAPI(config=env, sim=args.sim))
    #turpe = Turpe(constants=env)
    dm.process()
    exit()
    drafts = odoo.drafts
    drafts_df = pd.DataFrame(drafts)
    drafts_df.to_csv(enedis.dirs['R15'].joinpath('drafts.csv'))
    
    # Deprecated since logs will not be written in odoo anymore
    #log_id = odoo.write('x_log_enedis', r15.to_x_log_enedis())[0]

    consos = releves[releves['traitable_automatiquement'] == True].set_index(['pdl'])

    # On ajoute "puissance_souscrite" aux consos.
    merged = pd.merge(drafts_df, consos, on='pdl')
    merged.to_csv(enedis.dirs['R15'].joinpath('merged.csv'))

    complete = turpe.compute(merged).set_index(['pdl'])
    lines = pd.DataFrame(odoo.get_lines()).set_index(['pdl'])

    # TODO Faire des Vérifications sur les données

    no_data = []
    lines_to_inject = []
    invoices_to_inject = []
    for d in drafts:
        if d['pdl'] not in complete.index or (d['pdl'] in complete.index.values
                                                and not complete.at[d["pdl"], 'traitable_automatiquement']):
            
            no_data += [d['pdl']]
            continue
        
        invoices_to_inject = [{'id': d['id'], #'x_log_id': log_id, 
                               'x_turpe' : complete.at[d['pdl'],'turpe'], 
                               'x_type_compteur': complete.at[d['pdl'],'Type_Compteur'],
                               'x_scripted': True}]

        to_update = lines.loc[d["pdl"]].set_index(['code'])

        # On enlève les dates de la ligne
        abo = to_update.loc['ABO', :]
        lines_to_inject += [{'id': abo['id'], 'name': abo['name'].split('-')[0], 'deferred_start_date': str(starting_date), 'deferred_end_date': str(ending_date)}]
        lines_to_inject += [{'id': to_update.at[False, 'id'], 'name': f"Dont {round(complete.at[d['pdl'],'turpe'], 2)}€ de taxes d'acheminement"}]

        if 'BASE' in to_update.index:
            lines_to_inject += [{'id': to_update.at['BASE', 'id'], 'quantity': sum(complete.loc[d["pdl"], ['HPH_conso', 'HCH_conso', 'HPB_conso', 'HCB_conso']])}]

        elif 'HP' in to_update.index and 'HC' in to_update.index:
            lines_to_inject += [{'id': to_update.at['HP', 'id'], 'quantity': sum(complete.loc[d["pdl"], ['HPH_conso', 'HPB_conso']])}]
            lines_to_inject += [{'id': to_update.at['HC', 'id'], 'quantity': sum(complete.loc[d["pdl"], ['HCH_conso', 'HCB_conso']])}]
    if no_data:
        _logger.warning(f'Pas de consommation pour les pdl suivants #{no_data}')

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
