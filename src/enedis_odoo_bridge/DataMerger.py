from typing import Dict, List
from datetime import date
import pandas as pd
import numpy as np
from pandas import DataFrame

from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.EnedisFluxEngine import EnedisFluxEngine
from enedis_odoo_bridge.utils import gen_dates, check_required
from enedis_odoo_bridge.consumption_estimators import BaseEstimator, LastFirstEstimator

import logging
_logger = logging.getLogger('enedis_odoo_bridge')

class DataMerger:
    def __init__(self, config: Dict[str, str], date:date, enedis: EnedisFluxEngine, odoo: OdooAPI) -> None:
        self.config = check_required(config, ['TURPE_B_CU4', 
                                              'TURPE_CG', 
                                              'TURPE_CC',
                                              'TURPE_TAUX_HPH_CU4', 
                                              'TURPE_TAUX_HCH_CU4', 
                                              'TURPE_TAUX_HPB_CU4', 
                                              'TURPE_TAUX_HCB_CU4',])
        self.enedis = enedis
        self.odoo = odoo

        self.starting_date, self.ending_date = gen_dates(date)


    def fetch_enedis_data(self, heuristic: BaseEstimator, columns: list[str])-> DataFrame:
        # Récupérer les données depuis EnedisFluxEngine
        return self.enedis.fetch(self.starting_date, self.ending_date, columns, heuristic=heuristic)

    def fetch_odoo_data(self)-> DataFrame:
        # Récupérer les données depuis OdooAPI
        return self.odoo.fetch_drafts()

    def merge_data(self, enedis_data: DataFrame, odoo_data: DataFrame)-> DataFrame:
        # Fusionner les données ici
        _logger.info(f"Merging data:")
        _logger.info(f"- {len(enedis_data)} enedis entries.")
        _logger.debug(enedis_data)
        _logger.info(f"- {len(odoo_data)} odoo entries.")
        _logger.debug(odoo_data)
        merged = pd.merge(odoo_data, enedis_data, left_on='x_pdl', right_on='pdl', how='left')
        _logger.debug(merged)
        return merged
    
    def add_taxes(self, data:DataFrame):
        data['turpe_fix'] = (data['x_puissance_souscrite'].astype(float) * float(self.config['TURPE_B_CU4'])
            + float(self.config['TURPE_CG']) + float(self.config['TURPE_CC']))/12
        
        cu4 = ~data[['HPH_conso', 'HPB_conso', 
                     'HCH_conso', 'HCB_conso']].isna().all(axis=1)
        data['turpe_var'] = (
            data['HPH_conso'].astype(float)*float(self.config['TURPE_TAUX_HPH_CU4'])*0.01
            + data['HCH_conso'].astype(float)*float(self.config['TURPE_TAUX_HCH_CU4'])*0.01
            + data['HPB_conso'].astype(float)*float(self.config['TURPE_TAUX_HPB_CU4'])*0.01
            + data['HCB_conso'].astype(float)*float(self.config['TURPE_TAUX_HCB_CU4'])*0.01)
        data['CTA'] = data['turpe_fix'] * 0.2193
        data['Assise'] = data['Base'] * 2.1 * 0.01
        # TODO Turpe pour les pas CU4
        return data

    def enrich(self, data: DataFrame)-> DataFrame:
        data['HP'] = data[['HPH_conso', 'HPB_conso', 'HP_conso']].sum(axis=1)
        data['HC'] = data[['HCH_conso', 'HCB_conso', 'HC_conso']].sum(axis=1)
        data['not_enough_data'] = data[['HPH_conso', 'HPB_conso', 'HCH_conso', 
            'HCB_conso', 'BASE_conso', 'HP_conso',
            'HC_conso']].isna().all(axis=1)
        data['Base'] = np.where(
            data['not_enough_data'],
            np.nan,
            data[['HPH_conso', 'HPB_conso', 'HCH_conso', 
            'HCB_conso', 'BASE_conso', 'HP_conso', 
            'HC_conso']].sum(axis=1)
        )
        _logger.debug(data)
        return data

    def update_odoo(self, data: DataFrame):
        # Mettre à jour Odoo avec les données fusionnées
        self.odoo.update_draft_invoices(data, self.starting_date, self.ending_date)

    def process(self, drafts: bool=True):
        enedis_data = self.enedis.fetch(self.starting_date, self.ending_date,
                                        columns=['Type_Compteur', 'Num_Serie', 'Date_Theorique_Prochaine_Releve'],
                                        heuristic=LastFirstEstimator())

        enedis_data.to_csv(self.enedis.root_path.joinpath('R15').joinpath(
            f'EnedisFluxEngine_from_{self.starting_date}_to{self.ending_date}.csv'))

        odoo_data = self.fetch_odoo_data() if drafts else self.odoo.fetch_orders()

        odoo_data.to_csv(self.enedis.root_path.joinpath('R15').joinpath(
            f'OdooAPI_from_{self.starting_date}_to{self.ending_date}.csv'))
        data = self.merge_data(enedis_data, odoo_data)
        
        data = self.enrich(data)
        data = self.add_taxes(data)
        data.to_csv(self.enedis.root_path.joinpath('R15').joinpath(
            f'DataMerger_from_{self.starting_date}_to{self.ending_date}.csv'))
        data[data['Base'].isna()].to_csv(self.enedis.root_path.joinpath('R15').joinpath(
            f'DataMerger_TOCHECK_from_{self.starting_date}_to{self.ending_date}.csv'))
        return data

    def process_and_update(self, drafts: bool=True):
        data = self.process(drafts)
        if drafts:
            self.update_odoo(data)
        else:
            self.odoo.update_sale_order(data, self.starting_date, self.ending_date)
        return data


