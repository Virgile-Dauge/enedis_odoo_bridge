import pandas as pd
from pathlib import Path
from datetime import date
from typing import Union, Any
from pandas import DataFrame

from enedis_odoo_bridge.enedis_flux_engine.flux_repository import BaseFluxRepository
from enedis_odoo_bridge.enedis_flux_engine.zip_repository import F15ZipRepository

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
    horodate : list[date] = [pd.to_datetime(zip_file.stem.split('_')[-1], format='%Y%m%d%H%M%S').date() for zip_file in zip_files]
    if end_date is None:
        return [z for z, h in zip(zip_files, horodate) if (h-start_date).days == 2]

    return [z for z, h in zip(zip_files, horodate) if (h-start_date).days >= 2 and (h-end_date).days <= 2]

class F15FluxRepository(BaseFluxRepository):
    def get_flux_by_date(self, start_date: date, end_date: date=None) -> DataFrame:
        zip_files = list(self.root_path.joinpath('F15').expanduser().glob('*.zip'))
        to_read = select_zip_by_date(zip_files, start_date, end_date=end_date)

        zip_repository = F15ZipRepository()
        dfs = [zip_repository.process_zip(z) for z in to_read]
        if dfs:
            return pd.concat(dfs)
        
        return DataFrame()
