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
        # TODO gérer les timezones pour plus grande précision de l'estimation
        #df['Date_Releve'] = df['Date_Releve'].dt.tz_convert(None)
        initial = df.loc[(df[('', 'meta', 'Date_Releve')] >= start)
                    & (df[('', 'meta', 'Date_Releve')] <= end)
                    & (df[('', 'meta', 'Statut_Releve')] == 'INITIAL')
                    ]
        
        initial['start_date'] = start
        initial['end_date'] = end

        pdls = initial.groupby('pdl', group_keys=True)

        consos = DataFrame({k+'_conso': pdls[k+'_index'].max()-pdls[k+'_index'].min() 
                            for k in ['HPH', 'HCH', 'HPB', 'HCB']})

        dates = DataFrame({
            'start_date': initial[(initial['Motif_Releve'] == 'CFNE') | (initial['Motif_Releve'] == 'MES')].groupby('pdl')['Date_Releve'].first(),
            'end_date': end})

        return pd.merge(consos, dates, on='pdl', how='left')