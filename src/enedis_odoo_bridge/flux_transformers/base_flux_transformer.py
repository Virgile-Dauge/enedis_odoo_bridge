from abc import ABC, abstractmethod

import os
import zipfile
import xmlschema
import pandas as pd

from pandas import DataFrame
from pathlib import Path
from typing import Any


class BaseFluxTransformer(ABC):
    def __init__(self, xsd_path: Path):
        self.schema = xmlschema.XMLSchema(xsd_path)
        self.data = DataFrame()

    def xml_to_dict(self, xml_path: Path)-> dict[str, Any]:
        return self.schema.to_dict(xml_path)

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
                    full_path = os.path.join('temp_dir', filename)
                    # Convertir le XML en DataFrame
                    xml_dict = self.xml_to_dict(full_path)
                    df = self.dict_to_dataframe(xml_dict)
                    #for column in df.columns:
                    #    if 'date' in column.lower() or 'datetime' in column.lower():
                    #        df[column] = pd.to_datetime(df[column], errors='coerce')
                    #non_scalar_columns = [col for col in df.columns if any(df[col].apply(lambda x: isinstance(x, (list, dict))))]
                    #df = df.drop(non_scalar_columns, axis=1)
                    dfs.append(df)
                    # Optionnel : Supprimer le fichier temporaire si désiré
                    #os.remove(full_path)
            # Concaténer toutes les DataFrames
            if dfs:
                concat = pd.concat(dfs, ignore_index=True).reset_index(drop=True)
                return concat
            else:
                return DataFrame()
            
    def add_zip(self, zip_path: Path)-> None:
        """
        Add a zip file to the transformer.

        Parameters:
        zip_path (Path): The path to the zip file to be added.
        """
        self.data = pd.concat([self.data, self.process_zip(zip_path)])
