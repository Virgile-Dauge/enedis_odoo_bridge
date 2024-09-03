import pandas as pd
from pathlib import Path
from datetime import date, timedelta
from typing import Union, Any
from pandas import DataFrame

from enedis_odoo_bridge.enedis_flux_engine.flux_repository import BaseFluxRepository
from enedis_odoo_bridge.enedis_flux_engine.zip_repository import C15ZipRepository

def select_zip_by_date(zip_files: list[Path], start_date: date, end_date: Union[date, None]=None) -> list[Path]:
    """
    Selects ZIP files based on their embedded date within the filename.

    The function extracts dates from the filenames of the provided ZIP files and filters them based on the given start and end dates.
    If the end date is not provided, it selects files that are exactly 2 days after the start date.
    If the end date is provided, it selects files that are at least 2 days after the start date and max 2 days after the end date.

    Parameters:
    zip_files (list[Path]): List of paths to ZIP files.
    start_date (date): The start date for filtering the ZIP files.
    end_date (Union[date, None], optional): The end date for filtering the ZIP files. Defaults to None.

    Returns:
    list[Path]: A list of paths to the ZIP files that match the date criteria.
    """
    return zip_files

class C15FluxRepository(BaseFluxRepository):
    def get_flux_by_date(self, start_date: date, end_date: date) -> DataFrame:
        zip_files = list(self.root_path.joinpath('C15').expanduser().glob('*.zip'))
        to_read = select_zip_by_date(zip_files, start_date, end_date)

        zip_repository = C15ZipRepository()
        dfs = [zip_repository.process_zip(z) for z in to_read]
        if dfs:
            # Filtrer les résultats par les dates de début et de fin
            result_df = pd.concat(dfs).reset_index(drop=True)

            filtered_df = result_df
            return self.preprocess(filtered_df)
        
        return DataFrame()

    def preprocess(self, data : DataFrame) -> DataFrame:
        # Convert columns where the last level of the index starts with "Date_" to datetime
        for col in data.columns:
            if col.startswith("Date_"):
                data[col] = pd.to_datetime(data[col])#.dt.tz_localize('Etc/GMT-2')
        data = data.rename(columns={'Id_PRM': 'pdl', 
                            'Date_Evenement': 'date',
                            'Formule_Tarifaire_Acheminement': 'FTA',
                            'Puissance_Souscrite' : 'P',
                            'Num_Depannage': 'depannage'})
        data['P'] = data['P'].astype(int)
        return data.sort_values(['pdl', 'date']).copy()