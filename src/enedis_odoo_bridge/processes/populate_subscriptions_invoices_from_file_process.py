import logging
import numpy as np
import pandas as pd
from pandas import DataFrame, Timestamp
from datetime import date
from pathlib import Path

from enedis_odoo_bridge.processes import BaseProcess
from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.EnedisFluxEngine import EnedisFluxEngine
from enedis_odoo_bridge.utils import gen_Timestamps, check_required
from enedis_odoo_bridge.consumption_estimators import LastFirstEstimator


class PopulateSubscriptionsInvoicesFromFileProcess(BaseProcess):
    def __init__(self,
                config: dict[str, str], enedis: EnedisFluxEngine,
                odoo: OdooAPI,
                date: date, 
                data_path: Path, 
                logger: logging.Logger=logging.getLogger('enedis_odoo_bridge')) -> None:
        super().__init__(config, enedis) 
        self.filter = filter
        self.odoo = odoo
        self.starting_date, self.ending_date = gen_Timestamps(date)
        self.data_path = data_path
        
    def run(self):
        consumptions = pd.read_csv(self.data_path)[['pdl', 'F_HP', 'F_HC', 'F_BASE', 'TURPE']].fillna(0)
        consumptions['F_HP'] = consumptions['F_HP'].astype(int)
        consumptions['F_HC'] = consumptions['F_HC'].astype(int)
        consumptions['F_BASE'] = consumptions['F_BASE'].astype(int)
        consumptions['TURPE'] = consumptions['TURPE'].apply(lambda x: float(str(x).replace(',', '.')))
        consumptions['pdl'] = consumptions['pdl'].apply(lambda x: f"{int(x)}")
        consumptions = consumptions.dropna(subset=['pdl'])
        consumptions = consumptions[consumptions['pdl'] != "0"]
        consumptions['not_enough_data'] = False
        consumptions = consumptions.rename(columns={'F_HP': 'HP', 'F_HC': 'HC', 'F_BASE': 'Base', 'TURPE': 'x_turpe'})
        print(consumptions)


        # Récup données Odoo
        draft_orders = self.odoo.search_read('sale.order', filters=[[['x_invoicing_state', '=', 'draft']]], fields=['id', 'x_pdl', 'invoice_ids', 'x_lisse'])

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

        # Merge les 3 sources
        merged_data = pd.merge(odoo_data, consumptions, left_on='x_pdl', right_on='pdl', how='inner').drop(columns=['pdl'])
        # Merging all data
        merged_data = pd.merge(merged_data, enedis_data, left_on='x_pdl', right_on='pdl', how='inner').drop(columns=['pdl'])
        print(merged_data)

        self.odoo.update_draft_invoices(merged_data, self.starting_date, self.ending_date)



