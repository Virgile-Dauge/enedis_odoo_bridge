from abc import ABC, abstractmethod
from pandas import Timestamp, DataFrame, Series
from typing import Dict, List, Any
# Interface commune pour les stratégies
class Strategy(ABC):
    @abstractmethod
    def get_strategy_name(self):
        pass
    @abstractmethod
    def estimate_consumption(self, data: Dict[str, DataFrame], start: Timestamp, end: Timestamp) -> DataFrame:
        pass


# Implémentation de différentes stratégies
class StrategyMaxMin(Strategy):
    def get_strategy_name(self):
        return 'Max - Min of available indexes'
    def estimate_consumption(self, data: Dict[str, DataFrame], start: Timestamp, end: Timestamp) -> DataFrame:
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
        df = data['R15']
        # TODO gérer les timezones pour plus grande précision de l'estimation
        df['Date_Releve'] = df['Date_Releve'].dt.tz_convert(None)

        initial = df.loc[(df['Date_Releve'] >= start)
                    & (df['Date_Releve'] <= end)
                    & (df['Statut_Releve'] == 'INITIAL')]

        pdls = initial.groupby('pdl')

        # Pour chaque pdl, on fait la différence entre le plus grand et le plus petit des index pour chaque classe de conso.
        consos = DataFrame({k+'_conso': pdls[k+'_index'].max()-pdls[k+'_index'].min() 
                            for k in ['HPH', 'HCH', 'HPB', 'HCB']})
        return consos

class StrategyAugmentedMaxMin(Strategy):
    def get_strategy_name(self):
        return 'Max - Min of available indexes, missing days are remplaced by mean daily consumption'
    def estimate_consumption(self, data: Dict[str, DataFrame], start: Timestamp, end: Timestamp) -> DataFrame:
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
        df = data['R15']
        # TODO gérer les timezones pour plus grande précision de l'estimation
        df['Date_Releve'] = df['Date_Releve'].dt.tz_convert(None)

        initial = df.loc[(df['Date_Releve'] >= start)
                    & (df['Date_Releve'] <= end)
                    & (df['Statut_Releve'] == 'INITIAL')]

        # TODO Compter le nombre de jours manquants.
        # TODO Ajouter la moyenne des consos/jours*nb jours manquants pour chaque pdl
        res = {}
        pdls = initial.groupby('pdl')

        indices_min_par_groupe = pdls.apply(lambda x: x['Date_Releve'].min())
        indices_max_par_groupe = pdls.apply(lambda x: x['Date_Releve'].max())
        for pdl, group in initial.groupby('pdl'):
            # Find min record

            # Find max record
            ...

        # Pour chaque pdl, on fait la différence entre le plus grand et le plus petit des index pour chaque classe de conso.
        consos = DataFrame({k+'_conso': pdls[k+'_index'].max()-pdls[k+'_index'].min() 
                            for k in ['HPH', 'HCH', 'HPB', 'HCB']})
        return consos



