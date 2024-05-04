
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

        drafts = self.odoo.fetch_drafts()
        self.logger.extra['prefix'] = ''
        self.logger.info(f"├──Merging data:")
        self.logger.info(f"│   ├──{len(services)} enedis entries.")
        self.logger.debug(services)
        self.logger.info(f"│   └──{len(drafts)} odoo entries.")
        self.logger.debug(drafts)

        data = pd.merge(services, drafts, left_on='pdl', right_on='x_pdl', how='left')
        self.logger.debug(data)
        data.to_csv(self.enedis.root_path.joinpath('F15').joinpath(
            f'Services_from_{self.starting_date.strftime("%Y-%m-%d")}_to_{self.ending_date.strftime("%Y-%m-%d")}.csv'))
        
        # TODO 
        # Pour chacun des produits enedis, trouver le produit correspondant dans Odoo

        products = self.odoo.execute('product.template', 'search_read', 
            [[['x_enedis_id', '=', 'F180O3C5M']]], 
            {})
        print(products)

        # TODO
        # Pour chacune des lignes de facture enedis, ajouter dans la facture brouillon une ligne avec le produit Odoo adapté
        # └── Vérif si ligne déjà présente dans la facture brouillon, si ou verif quantitié
        #       ├── Sinon Création des lignes de facture
        #       └── update des invoice_line_ids dans la facture brouillon





        
        
