
import logging
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import date

from enedis_odoo_bridge.processes import BaseProcess
from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.EnedisFluxEngine import EnedisFluxEngine
from enedis_odoo_bridge.utils import gen_dates, check_required, CustomLoggerAdapter
from enedis_odoo_bridge.consumption_estimators import LastFirstEstimator


_logger = logging.getLogger('enedis_odoo_bridge')
_logger = CustomLoggerAdapter(_logger, {"prefix": ""})

class UpdateValuesInDraftInvoicesProcess(BaseProcess):
    def __init__(self, config: dict[str, str], enedis: EnedisFluxEngine, odoo: OdooAPI, date: date) -> None:
        self.config = config
        self.enedis = enedis
        self.odoo = odoo
        self.will_update_production_db = True

        self.config = check_required(config, ['TURPE_B_CU4', 
                                              'TURPE_CG', 
                                              'TURPE_CC',
                                              'TURPE_TAUX_HPH_CU4', 
                                              'TURPE_TAUX_HCH_CU4', 
                                              'TURPE_TAUX_HPB_CU4', 
                                              'TURPE_TAUX_HCB_CU4',])

        self.starting_date, self.ending_date = gen_dates(date)

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
    
    def run(self):
        _logger.info(f"Running UpdateValuesInDraftInvoicesProcess :")
        _logger.extra['prefix'] = ' │   '
        enedis_data = self.enedis.fetch(self.starting_date, self.ending_date,
                                        columns=['Type_Compteur', 'Num_Serie', 'Date_Theorique_Prochaine_Releve'],
                                        heuristic=LastFirstEstimator())
        
        enedis_data.to_csv(self.enedis.root_path.joinpath('R15').joinpath(
            f'EnedisFluxEngine_from_{self.starting_date}_to{self.ending_date}.csv'))
        
        odoo_data = self.odoo.fetch_drafts()

        odoo_data.to_csv(self.enedis.root_path.joinpath('R15').joinpath(
            f'OdooAPI_from_{self.starting_date}_to{self.ending_date}.csv'))
        
        _logger.info(f" ├── Merging data:")
        _logger.info(f" │   ├── {len(enedis_data)} enedis entries.")
        _logger.debug(enedis_data)
        _logger.info(f" │   └── {len(odoo_data)} odoo entries.")
        _logger.debug(odoo_data)
        data = pd.merge(odoo_data, enedis_data, left_on='x_pdl', right_on='pdl', how='left')
        _logger.debug(data)
        
        data = self.enrich(data)
        data = self.add_taxes(data)
        data.to_csv(self.enedis.root_path.joinpath('R15').joinpath(
            f'DataMerger_from_{self.starting_date}_to{self.ending_date}.csv'))
        data[data['Base'].isna()].to_csv(self.enedis.root_path.joinpath('R15').joinpath(
            f'DataMerger_TOCHECK_from_{self.starting_date}_to{self.ending_date}.csv'))
        
        _logger.info(f" └── updating odoo entries." + (" [simulated]" if self.odoo.sim else ""))
        self.odoo.update_draft_invoices(data, self.starting_date, self.ending_date)


        
        
