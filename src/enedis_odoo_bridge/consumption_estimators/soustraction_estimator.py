import pandas as pd
from pandas import Timestamp, DataFrame, Series
from typing import Dict, List, Any
from enedis_odoo_bridge.consumption_estimators import BaseEstimator

class SoustractionEstimator(BaseEstimator):
    def get_estimator_name(self):
        return 'Max - Min of available indexes'
    def estimate_consumption(self, meta: DataFrame, index: DataFrame, consos: DataFrame, start: Timestamp, end: Timestamp) -> DataFrame:
        """
        Estimates the total consumption per PDL for the specified period.

        :param self: Instance of the StrategyMinMax class.
        :param data: The dataframe containing mesures.
        :type data: pandas DataFrame
        :param start: The start date of the period.
        :type start: pandas Timestamp
        :param end: The end date of the period.
        :type end: pandas Timestamp
        :return: The total consumption for the specified period, on each 
        :rtype: pandas DataFrame

        Idée : On filtre les relevés de la période, avec Statut_Releve = 'INITIAL'. 
        On les regroupe par pdl, puis pour chaque groupe, 
            on fait la différence entre le plus grand et le plus petit index pour chaque classe de conso.

            Pour l'instant on ne vérifie rien. Voyons quelques cas :
            - Si pas de relevés ?
            - Si un seul relevé, conso = 0 Alors qu'il faudrait NaN.
            - Si plusieurs relevés, conso ok (sauf si passage par zéro du compteur ou coef lecture != 1)
        """
        dates = self.initialize_dates(meta, start, end)
        # Filter by 'Date_Releve' and 'Statut_Releve = 'INITIAL'
        filter = (meta['Date_Releve'] >= start) & (meta['Date_Releve'] <= end) & (meta['Statut_Releve'] == 'INITIAL')      
        # Group by 'pdl' and calculate consumption for each category
        estimates = index[filter].groupby('pdl').apply(lambda x: pd.Series({
            'HPH_conso': x['HPH_Valeur'].max() - x['HPH_Valeur'].min(),
            'HCH_conso': x['HCH_Valeur'].max() - x['HCH_Valeur'].min(),
            'HPB_conso': x['HPB_Valeur'].max() - x['HPB_Valeur'].min(),
            'HCB_conso': x['HCB_Valeur'].max() - x['HCB_Valeur'].min(),
            'Base_conso': x['BASE_Valeur'].max() - x['BASE_Valeur'].min(),
            'HP_conso': x['HP_Valeur'].max() - x['HP_Valeur'].min(),
            'HC_conso': x['HC_Valeur'].max() - x['HC_Valeur'].min(),
        })).reset_index()
        estimates = pd.merge(estimates, dates, on='pdl', how='left')
        # SI UN SEUL RELEVE, CONSO = NaN
        return estimates