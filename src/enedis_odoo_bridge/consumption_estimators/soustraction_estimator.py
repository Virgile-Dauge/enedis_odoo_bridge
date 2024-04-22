import pandas as pd
from pandas import Timestamp, DataFrame, Series
from typing import Dict, List, Any
from enedis_odoo_bridge.consumption_estimators import BaseEstimator

class SoustractionEstimator(BaseEstimator):
    def get_estimator_name(self):
        return 'Max - Min of available indexes'
    def estimate_consumption(self, df: DataFrame, start: Timestamp, end: Timestamp) -> DataFrame:
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
            - Si un seul relevé, conso = 0
            - Si plusieurs relevés, conso ok (sauf si passage par zéro du compteur ou coef lecture != 1)
        """
        initial = df.loc[(df[('', 'meta', 'Date_Releve')] >= start)
                    & (df[('', 'meta', 'Date_Releve')] <= end)
                    & (df[('', 'meta', 'Statut_Releve')] == 'INITIAL')
                    ]
               
        # Group by 'pdl' and calculate consumption for each category
        grouped = initial.groupby(('', 'meta', 'pdl'))
        consos = grouped.apply(lambda x: pd.Series({
            'HPH_conso': x[('index', 'HPH', 'Valeur')].max() - x[('index', 'HPH', 'Valeur')].min(),
            'HCH_conso': x[('index', 'HCH', 'Valeur')].max() - x[('index', 'HCH', 'Valeur')].min(),
            'HPB_conso': x[('index', 'HPB', 'Valeur')].max() - x[('index', 'HPB', 'Valeur')].min(),
            'HCB_conso': x[('index', 'HCB', 'Valeur')].max() - x[('index', 'HCB', 'Valeur')].min(),
            'Base_conso': x[('index', 'BASE', 'Valeur')].max() - x[('index', 'BASE', 'Valeur')].min(),
            'HP_conso': x[('index', 'HP', 'Valeur')].max() - x[('index', 'HP', 'Valeur')].min(),
            'HC_conso': x[('index', 'HC', 'Valeur')].max() - x[('index', 'HC', 'Valeur')].min(),
        })).reset_index().rename(columns={('', 'meta', 'pdl'): 'pdl'})

        conditions = (initial[('', 'meta', 'Motif_Releve')] == 'CFNE') | (initial[('', 'meta', 'Motif_Releve')] == 'MES')
        starting_dates = initial[conditions][[('', 'meta', 'pdl'),('', 'meta', 'Date_Releve')]].groupby(('', 'meta', 'pdl')).min().reset_index()[('', 'meta', 'Date_Releve')]

        consos['start_date'] = starting_dates
        consos['end_date'] = end
        return consos