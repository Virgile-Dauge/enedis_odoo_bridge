
import logging
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import date
from rich import print, pretty, inspect

from enedis_odoo_bridge.processes import BaseProcess
from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.EnedisFluxEngine import EnedisFluxEngine
from enedis_odoo_bridge.utils import gen_Timestamps, check_required, CustomLoggerAdapter
from enedis_odoo_bridge.consumption_estimators import LastFirstEstimator


class AddEnedisServiceToDraftInvoiceProcess(BaseProcess):
    def __init__(self, config: dict[str, str], enedis: EnedisFluxEngine, odoo: OdooAPI, date: date, logger: logging.Logger=logging.getLogger('enedis_odoo_bridge')) -> None:
        self.config = config
        self.enedis = enedis
        self.odoo = odoo
        self.will_update_production_db = True
        self.logger = logger

        self.config = check_required(config, ['TURPE_B_CU4', 
                                              'TURPE_CG', 
                                              'TURPE_CC',
                                              'TURPE_TAUX_HPH_CU4', 
                                              'TURPE_TAUX_HCH_CU4', 
                                              'TURPE_TAUX_HPB_CU4', 
                                              'TURPE_TAUX_HCB_CU4',])

        self.starting_date, self.ending_date = gen_Timestamps(date)

    
    def run(self):
        self.logger.info(f"Running AddEnedisServiceToDraftInvoiceProcess :")
        self.logger.extra['prefix'] = '│   '
        services = self.enedis.fetch_services(self.starting_date, self.ending_date)

        pretty.pprint(services)
        odoo_data = self.odoo.fetch_drafts()
        
        
        self.logger.info(f"├── Updating odoo entries in {self.config['DB']} from {self.config['URL']}" + (" [simulated]" if self.odoo.sim else ""))
        self.logger.extra['prefix'] = '│   ├──'

        #self.odoo.update_draft_invoices(data, self.starting_date, self.ending_date)
        
        self.logger.extra['prefix'] = '│   '
        self.logger.info(f"└──Update odoo entries done.")
        self.logger.extra['prefix'] = ''
        self.logger.info(f"└──AddEnedisServiceToDraftInvoiceProcess done.")


        
        
