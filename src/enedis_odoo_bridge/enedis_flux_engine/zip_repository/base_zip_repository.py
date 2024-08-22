import os
import zipfile
import pandas as pd

from abc import ABC, abstractmethod
from pandas import DataFrame
from pathlib import Path
from typing import Any, Optional


class BaseZipRepository(ABC):
    #def __init__(self):
        #self.schema = xmlschema.XMLSchema(xsd_path)
    @abstractmethod
    def xml_to_dict(self, xml_path: Path)-> dict[str, Any]:
        pass

    @abstractmethod
    def dict_to_dataframe(self, data_dict: dict[str, Any])-> DataFrame:
        pass
    
    @abstractmethod
    def preprocess(self)-> None:
        pass
    
    def process_zip(self, zip_path: Path)-> DataFrame:
        if not zip_path.is_file():
            raise FileNotFoundError(f'File {zip_path} not found.')
        
        # Ouvrir l'archive ZIP
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Liste pour stocker les dataframes
            dfs = []
            for filename in z.namelist():
                if filename.endswith('.xml'):
                    # Extraction du fichier XML
                    z.extract(filename, 'temp_dir')
                    full_path = Path('temp_dir').joinpath(filename)
                    # Convertir le XML en DataFrame
                    xml_dict = self.xml_to_dict(full_path)
                    if xml_dict:
                        df = self.dict_to_dataframe(xml_dict)
                        #df['zip_file'] = zip_path.name
                        dfs.append(df)
                    # Optionnel : Supprimer le fichier temporaire si désiré
                    os.remove(full_path)
            # Concaténer toutes les DataFrames
            if dfs:
                concat = pd.concat(dfs, ignore_index=True).reset_index(drop=True)
                return concat
            else:
                return DataFrame()

    def preprocess(self, data: DataFrame)-> DataFrame:
        return data