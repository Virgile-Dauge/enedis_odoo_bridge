import zipfile
import pandas as pd
import xmlschema
import asyncio
import nest_asyncio

def ensure_nesting():
    # Check if an event loop is already running
    # Nécessaire pour utilisation dans un notebook
    if asyncio.get_event_loop().is_running():
        nest_asyncio.apply()

from abc import ABC, abstractmethod
from pandas import DataFrame
from pathlib import Path
from typing import Optional, Any
from io import BytesIO

class BaseFluxRepository(ABC):
    def __init__(self, path: Path, xsd_path: Path):
        """
        schema : Le schéma XSD utilisé pour valider les fichiers XML de ce flux spécifique.
        """
        self.schema = xmlschema.XMLSchema(xsd_path)
        self.path = path
    
    @abstractmethod
    def _select_zips(self) -> list[Path]:
        """Sélectionne les fichiers ZIP à traiter."""
        pass

    @abstractmethod
    def _filter_files(self, filenames: list[str]) -> list[str]:
        """Filtre les fichiers XML d'intérêt dans la liste des fichiers contenus dans les ZIP."""
        pass
    @abstractmethod
    def _dict_to_dataframe(self, data_dict: dict[str, Any]) -> DataFrame:
        pass
    
    def _spec_post_process(self, df: DataFrame, start_date, end_date):
        return df
    
    def get_flux_by_date(self, start_date, end_date=None) -> DataFrame:
        """Processus principal pour traiter les flux, reste synchrone."""
        
        zips = self._select_zips(start_date, end_date)
        ensure_nesting()
        df = asyncio.run(self._process_async(zips))
        df = self._post_process(df)
        df = self._spec_post_process(df, start_date, end_date)
        return df.copy()
    
    def _post_process(self, df: DataFrame) -> DataFrame:
        for col in df.columns:
            if col.startswith("Date_"):
                df[col] = pd.to_datetime(df[col]).dt.date
        
        return df
    
    async def _process_async(self, zips: list[Path]) -> DataFrame:
        """Processus asynchrone interne pour traiter les flux."""
        
        all_dfs = []
        for zip_path in zips:
            with zipfile.ZipFile(zip_path, 'r') as z:
                filenames = z.namelist()
                filtered_filenames = self._filter_files(filenames)
                # Utilisation d'asyncio.gather pour exécuter les lectures de fichiers XML en parallèle
                tasks = [self._process_file_async(z, filename) for filename in filtered_filenames]
                results = await asyncio.gather(*tasks)

                all_dfs.extend([df for df in results if df is not None])
        
        if all_dfs:
            return pd.concat(all_dfs, ignore_index=True).reset_index(drop=True)
        return pd.DataFrame()

    async def _process_file_async(self, z: zipfile.ZipFile, filename: str) -> Optional[DataFrame]:
        """Lit et traite un fichier XML en mémoire, de manière asynchrone."""
        loop = asyncio.get_running_loop()
        xml_content = await loop.run_in_executor(None, z.read, filename)  # Lecture asynchrone du contenu XML
        xml_dict = await loop.run_in_executor(None, self.schema.to_dict, BytesIO(xml_content))  # Conversion en dict de manière asynchrone
        return self._dict_to_dataframe(xml_dict)