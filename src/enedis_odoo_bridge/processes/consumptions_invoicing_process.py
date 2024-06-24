import logging
import numpy as np
import pandas as pd
from pandas import DataFrame, Timestamp
from datetime import date, datetime
from pathlib import Path

from enedis_odoo_bridge.processes import BaseProcess
from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.utils import gen_dates

from enedis_odoo_bridge.enedis_flux_engine import get_consumptions_by_date, get_r15_by_date, get_f15_by_date
from enedis_odoo_bridge.consumption_estimators import LastFirstEstimator

class ConsumptionsInvoicingProcess(BaseProcess):
    def __init__(self,
                config: dict[str, str],
                odoo: OdooAPI,
                date: date,
                logger: logging.Logger=logging.getLogger('enedis_odoo_bridge')) -> None:
        super().__init__(config, None) 
        self.filter = filter
        self.odoo = odoo
        self.will_update_production_db = True
        
    def run(self):
        enedis_flux_path : Path = Path('~/data/flux_enedis')
        starting_date = date(2024, 6, 1)
        ending_date = date(2024, 6, 22)
        
        consumptions = get_consumptions_by_date(enedis_flux_path, starting_date, ending_date)
        print(consumptions)

        consumptions.to_excel('coucou.xlsx')
        # Récup données Odoo
        draft_orders = self.odoo.search_read('sale.order', filters=[[['x_invoicing_state', '=', 'draft']]], fields=['id', 'x_pdl', 'invoice_ids', 'x_lisse'])

        if draft_orders.empty:
            raise ValueError('No draft order found')
        print(draft_orders)
        draft_orders['invoice_ids'] = draft_orders['invoice_ids'].apply(lambda x: max(x) if x else None)
        draft_orders = draft_orders.rename(columns={'sale.order_id': 'order_id', 'invoice_ids': 'move_id'})
        print(draft_orders)

        draft_invoices = self.odoo.read('account.move', ids=draft_orders['move_id'].to_list(), fields=['invoice_line_ids',])
        draft_orders['invoice_line_ids'] = draft_invoices['invoice_line_ids']
        print(draft_invoices)

        odoo_data = self.odoo.add_cat_fields(draft_orders, [])

        # Récup données Enedis
        columns = ['pdl', 'Type_Compteur', 'Num_Serie', 'Date_Theorique_Prochaine_Releve', 
                    'start_date', 'end_date', 'subscription_days', 'update_dates']
        enedis_data = self.enedis.fetch_estimates(self.starting_date, self.ending_date,
                                 columns=['Type_Compteur', 'Num_Serie', 'Date_Theorique_Prochaine_Releve'],
                                 heuristic=LastFirstEstimator())[columns]
        
        print(enedis_data)
        enedis_data.to_csv('enedis_data.csv')
        # Merge les 3 sources
        merged_data = pd.merge(odoo_data, consumptions, left_on='x_pdl', right_on='pdl', how='inner').drop(columns=['pdl'])
        # Merging all data
        merged_data = pd.merge(merged_data, enedis_data, left_on='x_pdl', right_on='pdl', how='inner').drop(columns=['pdl'])
        print(merged_data)
        merged_data.to_csv('merged_data.csv')
        self.odoo.update_draft_invoices(merged_data, self.starting_date, self.ending_date)
