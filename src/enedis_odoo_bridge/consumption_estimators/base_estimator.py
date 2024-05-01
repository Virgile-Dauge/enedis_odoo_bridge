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

        base_df['month_days'] = (end - start).days + 1
        

        # Merge the start and end dates into the base DataFrame
        base_df = pd.merge(base_df, start_dates, on='pdl', how='left', suffixes=('', '_updated'))
        base_df = pd.merge(base_df, end_dates, on='pdl', how='left',suffixes=('', '_updated'))

        # Update start_date only if there's a corresponding entry in start_date_updates
        base_df['start_date'] = base_df['start_date_updated'].fillna(base_df['start_date'])
        base_df['end_date'] = base_df['end_date_updated'].fillna(base_df['end_date'])

        # Define conditions for initializing start and end dates
        valid_releve_conditions = (meta['Date_Releve'] >= start) & (meta['Date_Releve'] <= end) & (meta['Statut_Releve'] == 'INITIAL')

        # Calculate first and last releve dates for each pdl
        first_releve_dates = meta[valid_releve_conditions].groupby('pdl')['Date_Releve'].min().reset_index(name='first_releve_date')
        last_releve_dates = meta[valid_releve_conditions].groupby('pdl')['Date_Releve'].max().reset_index(name='last_releve_date')

        # Merge the first and last releve dates into the base DataFrame
        base_df = pd.merge(base_df, first_releve_dates, on='pdl', how='left')
        base_df = pd.merge(base_df, last_releve_dates, on='pdl', how='left')

        # Count the number of actual days for each pdl
        base_df['subscription_days'] = base_df.apply(lambda row: (row['end_date'] - row['start_date']).days + 1, axis=1)

        base_df['consumption_days'] = base_df.apply(lambda row: (row['last_releve_date'] - row['first_releve_date']).days + 1, axis=1)

        base_df['update_dates'] = base_df['subscription_days'] != base_df['month_days']

        # TODO Add coverage : first valid index date and last valid index date, total number of days covered
        base_df.drop(columns=['start_date_updated', 'end_date_updated'], inplace=True)

        return base_df
    
    def augment_estimates(self, estimates: DataFrame)-> DataFrame:
        """
        Augments the estimates DataFrame with additional date information.

        :param estimates: DataFrame containing estimates.
        :param dates: DataFrame containing additional date information.
        :return: The augmented estimates DataFrame.
        """

        # Calculate the average daily consumption for each consumption type and multiply by subscription_days
        consumption_types = [col for col in estimates.columns if col.endswith('_conso')]
        for ctype in consumption_types:
            # Calculate average daily consumption
            estimates[ctype + '_avg_daily'] = estimates[ctype] / estimates['consumption_days']
            # Adjust total consumption based on subscription_days
            estimates[ctype + '_adjusted'] = estimates[ctype + '_avg_daily'] * estimates['subscription_days']

        return estimates
    
    def fetch(self, meta: DataFrame, index:DataFrame, consu: DataFrame, start: Timestamp, end: Timestamp)-> DataFrame:
        dates = self.initialize_dates(meta, start, end)
        estimates = self.estimate_consumption(meta, index, consu, start, end, dates)
        augmented = self.augment_estimates(estimates)
        return augmented