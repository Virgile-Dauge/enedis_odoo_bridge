import pandas as pd
from pandas import Timestamp, DataFrame, Series
from typing import Dict, List, Any
from enedis_odoo_bridge.consumption_estimators import BaseEstimator

class LastFirstEstimator(BaseEstimator):
    def get_estimator_name(self):
        return 'Last - First of available indexes for each temporal class'
    def estimate_consumption(self, meta: DataFrame, index: DataFrame, consos: DataFrame, start: Timestamp, end: Timestamp, dates:DataFrame=None) -> DataFrame:
        """
        Estimates the total consumption per PDL for the specified period using the first and last occurrence.

        :param self: Instance of the class.
        :param meta: Metadata DataFrame.
        :param index: Index DataFrame containing consumption data.
        :param consos: Not used in this implementation.
        :param start: The start date of the period.
        :param end: The end date of the period.
        :param dates: Optional DataFrame with additional date information.
        :return: The total consumption for the specified period, on each PDL.
        :rtype: pandas DataFrame
        """
        # Filter by 'Date_Releve' and 'Statut_Releve = 'INITIAL'
        filter = (meta['Date_Releve'] >= start) & (meta['Date_Releve'] <= end) & (meta['Statut_Releve'] == 'INITIAL')
        filtered_index = index[filter]
        filtered_meta = meta[filter]

        temporal_classes = [k for k in ['HPH', 'HCH', 'HPB', 'HCB', 'BASE', 'HP', 'HC'] if k+'_Valeur' in index.columns]

        ids_releves = filtered_meta.groupby('pdl').apply(lambda x: pd.Series({'first_releve': x.iloc[0]['Id_Releve'],
            'last_releve': x.iloc[-1]['Id_Releve'],})).reset_index()

        # Group by 'pdl' and calculate consumption for each category using the first and last occurrence
        estimates = filtered_index.groupby('pdl').apply(lambda x: pd.Series({
            k+'_conso': float('nan') if len(x) == 1 else x.iloc[-1][k+'_Valeur'] - x.iloc[0][k+'_Valeur']
                        + 10**x.iloc[0][k+'_Nb_Chiffres_Cadran'] * x[k+'_Indicateur_Passage_A_Zero'].max()
                        * x.iloc[0][k+'_Coefficient_Lecture'] for k in temporal_classes
        })).reset_index()
        estimates = pd.merge(estimates, ids_releves, on='pdl', how='left')

        if dates is not None:
            estimates = pd.merge(estimates, dates, on='pdl', how='left')

        return estimates