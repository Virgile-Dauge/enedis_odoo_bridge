
import logging
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import date
from rich import print, pretty, inspect
from pathlib import Path

from enedis_odoo_bridge.processes import BaseProcess
from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.EnedisFluxEngine import EnedisFluxEngine
from enedis_odoo_bridge.utils import gen_Timestamps, check_required, CustomLoggerAdapter
from enedis_odoo_bridge.consumption_estimators import LastFirstEstimator

from enedis_odoo_bridge.enedis_flux_engine import get_f15_by_date


class AddEnedisServiceToDraftInvoiceProcess(BaseProcess):
    def __init__(self, enedis: EnedisFluxEngine, odoo: OdooAPI, start_date: date, end_date: date, logger: logging.Logger=logging.getLogger('enedis_odoo_bridge')) -> None:

        self.enedis = enedis
        self.odoo = odoo
        self.will_update_production_db = True
        self.logger = logger

        self.start_date, self.end_date = start_date, end_date

    
    def run(self):
        self.logger.info(f"Running AddEnedisServiceToDraftInvoiceProcess :")
        self.logger.extra['prefix'] = '│   '
        services = get_f15_by_date(Path('~/data/flux_enedis'), self.start_date, self.end_date)
        self.logger.info(services)
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
        
        # Pour chacun des produits enedis, trouver le produit correspondant dans Odoo
        product_ids = {}
        grouped = data.groupby('Id_EV')
        for id_ev, group in grouped:
            # Recherche du produit dans Odoo par Id_EV
            expected_price = float(group['Prix_Unitaire'].iloc[0])
            tva = float(group['Taux_TVA_Applicable'].iloc[0])
            products = self.odoo.execute('product.template', 'search_read', 
                                        [[['x_enedis_id', '=', id_ev], ['list_price', '=', expected_price]]], 
                                        {'fields': ['name', 'list_price', 'taxes_id']})
            if not products:
                # Aucun produit trouvé ou le prix ne correspond pas, création d'un nouveau produit
                new_product_data = {
                    'name': group['Libelle_EV'].iloc[0],
                    'list_price': expected_price,  # Définir le prix attendu
                    'x_enedis_id': id_ev,
                    # Ajouter d'autres champs nécessaires ici
                }
                cat_id = self.odoo.execute('product.category', 'search_read', 
                                    [[['name', '=', 'Prestation-Enedis']]], 
                                    {'fields': ['id']})
                if cat_id:
                    new_product_data['categ_id'] = cat_id[0]['id']

                tax_id = self.odoo.execute('account.tax', 'search_read', 
                                    [[['name', '=', f'{tva:g}% G'], ['type_tax_use', '=', 'sale']]], 
                                    {'fields': ['id']})
                if tax_id:
                    new_product_data['taxes_id'] = [[4, tax_id[0]['id'], 0]]

                new_product_id = self.odoo.execute('product.template', 'create', [new_product_data])

                if new_product_id:
                    product_ids[id_ev] = new_product_id[0]
                self.logger.info(f"New product created with ID: {new_product_id} for Id_EV: {id_ev}")
            else:
                product_ids[id_ev] = products[0]['id']
                self.logger.info(f"Product found for Id_EV: {id_ev} with ID: {products[0]['id']}")

        # map associe chaque Id_EV à son ID de produit
        data['product_id'] = data['Id_EV'].map(product_ids)
        print(data)

        exploded = data.explode('line_id_Prestation-Enedis')
        print(exploded)
        # TODO
        # Pour chacune des lignes de facture enedis, ajouter dans la facture brouillon une ligne avec le produit Odoo adapté
        # └── Vérif si ligne déjà présente dans la facture brouillon, si ou verif quantitié
        #       ├── Sinon Création des lignes de facture
        #       └── update des invoice_line_ids dans la facture brouillon





        
        
