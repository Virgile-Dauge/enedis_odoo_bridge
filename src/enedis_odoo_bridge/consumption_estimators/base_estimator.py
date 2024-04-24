from abc import ABC, abstractmethod
import pandas as pd
from pandas import Timestamp, DataFrame
from typing import Dict, List, Any

# Interface commune pour les stratégies
class BaseEstimator(ABC):
    @abstractmethod
    def get_estimator_name(self):
        pass
    @abstractmethod
    def estimate_consumption(self, df: DataFrame, start: Timestamp, end: Timestamp) -> DataFrame:
        pass

    def initialize_dates(self, meta: DataFrame, start: Timestamp, end: Timestamp) -> DataFrame:
        """
        Initializes a DataFrame with 'pdl' and default 'start_date' and 'end_date' based on conditions in the meta DataFrame.

        :param meta: DataFrame containing metadata, including 'pdl', 'Date_Releve', and 'Motif_Releve'.
        :return: A DataFrame with 'pdl', 'start_date', and 'end_date' columns, initialized based on the meta DataFrame.
        """
        # Define conditions for initializing start and end dates
        start_date_condition = (meta['Motif_Releve'] == 'CFNE') | (meta['Motif_Releve'] == 'MES')
        end_date_condition = (meta['Motif_Releve'] == 'CFNS')

        # Initialize start_date and end_date for each pdl based on conditions
        start_dates = meta.loc[start_date_condition].groupby('pdl')['Date_Releve'].min().reset_index(name='start_date')
        end_dates = meta.loc[end_date_condition].groupby('pdl')['Date_Releve'].max().reset_index(name='end_date')

        # Create a base DataFrame with all unique pdls
        base_df = pd.DataFrame(meta['pdl'].unique(), columns=['pdl'])
        base_df['start_date'] = start
        base_df['end_date'] = end

        base_df['normal_days'] = (end - start).days + 1
        

        # Merge the start and end dates into the base DataFrame
        base_df = pd.merge(base_df, start_dates, on='pdl', how='left', suffixes=('', '_updated'))
        base_df = pd.merge(base_df, end_dates, on='pdl', how='left',suffixes=('', '_updated'))

        # Update start_date only if there's a corresponding entry in start_date_updates
        base_df['start_date'] = base_df['start_date_updated'].fillna(base_df['start_date'])
        base_df['end_date'] = base_df['end_date_updated'].fillna(base_df['end_date'])

        # Count the number of actual days for each pdl
        base_df['actual_days'] = base_df.apply(lambda row: (row['end_date'] - row['start_date']).days + 1, axis=1)

        base_df['update_dates'] = base_df['actual_days'] != base_df['normal_days']

        # TODO Add coverage : first valid index date and last valid index date, total number of days covered
        base_df.drop(columns=['start_date_updated', 'end_date_updated'], inplace=True)

        return base_df