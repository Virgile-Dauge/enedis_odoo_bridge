import pandas as pd

from datetime import date
from pandas import DataFrame
from pathlib import Path
from typing import Union

from .flux_repository import BaseFluxRepository, FluxRepositoryFactory
import logging

_logger = logging.getLogger('enedis_odoo_bridge')

def get_consumptions_by_date(root_path: Path, start_date: date, end_date: Union[date, None]=None) -> DataFrame:
    flux_repository : BaseFluxRepository = FluxRepositoryFactory().get_flux_repository('R151', root_path)
    start : DataFrame = flux_repository.get_flux_by_date(start_date)
    end : DataFrame = flux_repository.get_flux_by_date(end_date)

    _logger.info(f'Computing comsumptions from {start_date} to {end_date}')
    if start.empty or end.empty:
        _logger.info(f'One of the following is empty : start ({len(start)} entries) and end ({len(end)} entries)') 
        return DataFrame()
    
    start = start.set_index('pdl')
    end = end.set_index('pdl')
    
    # Identify common PDLs
    common_pdls = start.index.intersection(end.index)
    _logger.info(f'#{len(common_pdls)} matched between start ({len(start)} entries) and end ({len(end)} entries) ')

    #all_data : DataFrame = flux_repository.get_flux_by_date(start_date, end_date)
    #all_data.to_excel('all.xlsx')
    #print(len(all_data['pdl'].unique()))

    if common_pdls.empty:
        return DataFrame()
    
    # Calculate the difference for specified columns
    columns_of_interest = ['HCB', 'HCH', 'HPB', 'HPH', 'HC', 'HP']
    differences = end.loc[common_pdls, columns_of_interest] - start.loc[common_pdls, columns_of_interest]
    return differences

def get_r15_by_date(root_path: Path, start_date: date, end_date: Union[date, None]=None) -> DataFrame:
    flux_repository : BaseFluxRepository = FluxRepositoryFactory().get_flux_repository('R15', root_path)
    return flux_repository.get_flux_by_date(start_date, end_date)

def get_f15_by_date(root_path: Path, start_date: date, end_date: Union[date, None]=None) -> DataFrame:
    flux_repository : BaseFluxRepository = FluxRepositoryFactory().get_flux_repository('F15', root_path)
    return flux_repository.get_flux_by_date(start_date, end_date)

def get_r151_by_date(root_path: Path, date: date) -> DataFrame:
    flux_repository : BaseFluxRepository = FluxRepositoryFactory().get_flux_repository('R151', root_path)
    return flux_repository.get_flux_by_date(date)

def get_c15_by_date(root_path: Path, start_date: date, end_date: Union[date, None]=None) -> DataFrame:
    flux_repository : BaseFluxRepository = FluxRepositoryFactory().get_flux_repository('C15', root_path)
    return flux_repository.get_flux_by_date(start_date, end_date)

def get_meta_from_r15(df : DataFrame) -> DataFrame:
    df['Date_Releve'] = pd.to_datetime(df['Date_Releve'])

    # Trouver l'indice de la Date_Releve la plus récente pour chaque pdl
    idx = df.groupby('pdl')['Date_Releve'].idxmax()
    
    # Sélectionner les lignes correspondant aux indices trouvés
    return df.loc[idx, ['pdl', 'Type_Compteur', 'Num_Serie']].set_index('pdl')

def get_CF_from_r15(df : DataFrame) -> tuple[DataFrame]:
    start_date_condition = ((df['Motif_Releve'] == 'CFNE') | (df['Motif_Releve'] == 'MES'))
    end_date_condition = (df['Motif_Releve'] == 'CFNS')

    start_dates = df.loc[start_date_condition].groupby('pdl')['Date_Releve'].min().reset_index(name='Date_Releve')
    end_dates = df.loc[end_date_condition].groupby('pdl')['Date_Releve'].max().reset_index(name='Date_Releve')

    # Ajout des colonnes qui commencent avec 'index.' et finissent avec '.Valeur'
    index_columns = [col for col in df.columns if col.startswith('index.') and col.endswith('.Valeur')]
    start_dates = start_dates.merge(df.loc[start_date_condition, ['pdl'] + index_columns].drop_duplicates(subset='pdl'), on='pdl', how='left')
    end_dates = end_dates.merge(df.loc[end_date_condition, ['pdl'] + index_columns].drop_duplicates(subset='pdl'), on='pdl', how='left')
    # Enlever 'index.' et '.Valeur' des noms des colonnes
    start_dates.columns = [col.replace('index.', '').replace('.Valeur', '') for col in start_dates.columns]
    end_dates.columns = [col.replace('index.', '').replace('.Valeur', '') for col in end_dates.columns]
    return start_dates, end_dates