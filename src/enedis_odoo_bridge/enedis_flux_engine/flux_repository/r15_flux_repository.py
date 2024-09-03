import pandas as pd
from pathlib import Path
from datetime import date
from typing import Union, Any
from pandas import DataFrame, Series

from enedis_odoo_bridge.enedis_flux_engine.flux_repository import BaseFluxRepository
from enedis_odoo_bridge.enedis_flux_engine.zip_repository import R15ZipRepository

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
    horodate : list[date] = [pd.to_datetime(zip_file.stem.split('_')[-1], format='%Y%m%d%H%M%S').date() for zip_file in zip_files]
    if end_date is None:
        print([z for z, h in zip(zip_files, horodate) if (h-start_date).days == 1 or (h-start_date).days == 2])
        return [z for z, h in zip(zip_files, horodate) if (h-start_date).days == 1 or (h-start_date).days == 2]

    return [z for z, h in zip(zip_files, horodate) if (h-start_date).days >= 2 and (h-end_date).days <= 2]

class R15FluxRepository(BaseFluxRepository):
    def get_flux_by_date(self, start_date: date, end_date: date=None) -> DataFrame:
        zip_files = list(self.root_path.joinpath('R15').expanduser().glob('*.zip'))
        to_read = select_zip_by_date(zip_files, start_date, end_date)

        zip_repository = R15ZipRepository()
        dfs = [zip_repository.process_zip(z) for z in to_read]
        if dfs:
            concat : DataFrame = pd.concat(dfs)
            to_rename : dict[str, str]= {c: c.replace('.meta.', '') for c in concat.columns if c.startswith('.meta.')}
            concat = concat.rename(columns=to_rename)
            concat['Date_Releve'] = pd.to_datetime(concat['Date_Releve']).apply(lambda x: x.date())
            filter : Series[bool]= (concat['Date_Releve'] >= start_date) & (concat['Date_Releve'] <= end_date)
            return self.preprocess(concat[filter]).copy()
        
        return DataFrame()

    def compress_serial_number(self, data: DataFrame)-> DataFrame:
        # Function to check if all 'Num_Serie' values in a row are the same and return the value if true
        def check_num_serie_uniformity(row):
            unique_values = row.dropna().unique().astype(str)
            if len(unique_values) == 1:
                return unique_values[0]
            else:
                raise ValueError("Different 'Num_Serie' values found within the same row.")

        # Apply the function across the DataFrame to create a new 'Num_Serie' column
        # Extract only the 'Num_Serie' columns for this operation
        num_serie_columns = [col for col in data.columns if col.endswith('Num_Serie')]
        data['Num_Serie'] = data[num_serie_columns].apply(check_num_serie_uniformity, axis=1)
        # Optionally, drop the original 'Num_Serie' columns if they are no longer needed
        return data.drop(columns=num_serie_columns)
    
    def preprocess(self, data : DataFrame) -> DataFrame:
        res : DataFrame = data.sort_values(by=['pdl', 'Date_Releve'],)
        res = res.reset_index(drop=True)

        res = self.compress_serial_number(res)
        to_drop_keys : list[str] = ['Libelle_Calendrier_Distributeur',
                   'Num_Sequence',
                   'Id_Calendrier_Distributeur',
                   'Id_Calendrier',
                   'Libelle_Calendrier',
                   'Niveau_Ouverture_Services',
                   'Nature_Consommation',
                   'Id_Releve_Precedent',
                   'Date_Releve_Precedent',
                   'Motif_Releve_Precedent',
                   'Nature_Index_Precedent',
                   'Libelle_Structure_Horosaisonniere',
                   'Id_Structure_Horosaisonniere',
                   ]
        to_drop = [c for c in res.columns if c.startswith('conso') or c in to_drop_keys]
        # Convert columns where the last level of the index starts with "Date_" to datetime
        for col in res.columns:
            if col.startswith("Date_"):
                res[col] = pd.to_datetime(res[col])
            # Convert all "index" and "conso" values to float
        for col in res.columns:
            if col.endswith('.Valeur'):
                res[col] = res[col].astype(float)
        return res.drop(columns=to_drop)
