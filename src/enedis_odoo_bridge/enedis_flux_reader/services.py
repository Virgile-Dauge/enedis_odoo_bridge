from datetime import date
from pandas import DataFrame
from pathlib import Path

from .flux_repository import R151FluxRepository

def get_consumptions_by_date(root_path: Path, start_date: date, end_date: date=None) -> DataFrame:
        flux_repository = R151FluxRepository(root_path)
        start : DataFrame = flux_repository.get_flux_by_date(start_date)
        end : DataFrame = flux_repository.get_flux_by_date(end_date)

        if start.empty or end.empty:
            return DataFrame()
        
        start = start.set_index('pdl')
        end = end.set_index('pdl')
        # Identify common PDLs
        common_pdls = start.index.intersection(end.index)
        if common_pdls.empty:
            return DataFrame()
        
        # Calculate the difference for specified columns
        columns_of_interest = ['HCB', 'HCH', 'HPB', 'HPH', 'HC', 'HP']
        differences = end.loc[common_pdls, columns_of_interest] - start.loc[common_pdls, columns_of_interest]
        return differences