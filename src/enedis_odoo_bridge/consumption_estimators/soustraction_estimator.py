import pandas as pd
from pandas import Timestamp, DataFrame, Series
from typing import Dict, List, Any
from enedis_odoo_bridge.consumption_estimators import BaseEstimator

class SoustractionEstimator(BaseEstimator):
    def get_estimator_name(self):
        return 'Max - Min of available indexes for each temporal class'
    def estimate_consumption(self, meta: DataFrame, index: DataFrame, consos: DataFrame, start: Timestamp, end: Timestamp, dates:DataFrame=None) -> DataFrame:
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
            - Si pas de relevés Empty DataFrame
            - Si un seul relevé, conso = 0 Alors qu'il faudrait NaN.
            - Si plusieurs relevés, conso ok
        """
        # Filter by 'Date_Releve' and 'Statut_Releve = 'INITIAL'
        filter = (meta['Date_Releve'] >= start) & (meta['Date_Releve'] <= end) & (meta['Statut_Releve'] == 'INITIAL')

        temporal_classes = [k for k in ['HPH', 'HCH', 'HPB', 'HCB', 'BASE', 'HP', 'HC'] if k+'_Valeur' in index.columns]
        
        # Group by 'pdl' and calculate consumption for each category
        estimates = index[filter].groupby('pdl').apply(lambda x: pd.Series({
            k+'_conso': abs(x[k+'_Valeur'].max() - x[k+'_Valeur'].min() 
                         - 10**x[k+'_Nb_Chiffres_Cadran'].max() * x[k+'_Indicateur_Passage_A_Zero'].max()) 
                         * x[k+'_Coefficient_Lecture'].max() for k in temporal_classes
        })).reset_index()

        if dates is not None:
            estimates = pd.merge(estimates, dates, on='pdl', how='left')
        # SI UN SEUL RELEVE, CONSO = NaN
        return estimates