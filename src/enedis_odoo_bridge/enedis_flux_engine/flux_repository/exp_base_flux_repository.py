import os
import zipfile
import pandas as pd
import xmlschema
import asyncio

from abc import ABC, abstractmethod
from pandas import DataFrame
from pathlib import Path
from typing import List, Any, Optional
from io import BytesIO
from datetime import date, timedelta

class ExpBaseFluxRepository(ABC):
    def __init__(self, path: Path, xsd_path: Path):
        """
        schema : Le schéma XSD utilisé pour valider les fichiers XML de ce flux spécifique.
        """
        self.schema = xmlschema.XMLSchema(xsd_path)
        self.path = path
    
    @abstractmethod
    def _select_zips(self) -> List[Path]:
        """Sélectionne les fichiers ZIP à traiter."""
        pass

    @abstractmethod
    def _filter_files(self, filenames: List[str]) -> List[str]:
        """Filtre les fichiers XML d'intérêt dans la liste des fichiers contenus dans les ZIP."""
        pass
    @abstractmethod
    def _dict_to_dataframe(self, data_dict: dict[str, Any]) -> DataFrame:
        pass
    
    def _spec_post_process(self, df: DataFrame, start_date, end_date):
        return df
    
    def process(self, start_date, end_date=None) -> DataFrame:
        """Processus principal pour traiter les flux, reste synchrone."""
        
        zips = self._select_zips(start_date, end_date)
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

# Autre exemple pour un autre type de flux
class F15DetailFluxRepository(ExpBaseFluxRepository):
    def __init__(self, path: Path):
        # Initialisation du schéma XSD spécifique au flux
        super().__init__(path=path.expanduser() / 'F15', xsd_path=Path(__file__).parent / 'schemas/GRD.XSD.0299.Flux_F15_Donnees_Detail_v3.3.2.xsd')

    def _select_zips(self, start_date, end_date) -> List[Path]:
        
        marge_passe = timedelta(days=60)
        marge_futur = timedelta(days=30)

        # Calculer les dates avec marges
        start_date_with_margin = start_date - marge_passe
        end_date_with_margin = (end_date + marge_futur) if end_date else (start_date + marge_futur)

        zip_files =list(self.path.glob("*.zip"))

        horodate = [pd.to_datetime(zip_file.stem.split('_')[-1], format='%Y%m%d%H%M%S').date() for zip_file in zip_files]

        return [z for z, h in zip(zip_files, horodate) if start_date_with_margin <= h <= end_date_with_margin]

    def _filter_files(self, filenames: List[str]) -> List[str]:
        # Implémentez la logique spécifique pour filtrer les fichiers XML d'intérêt
        return [f for f in filenames if not f.endswith('FA.xml')]

    def _dict_to_dataframe(self, data_dict: dict[str, Any]) -> DataFrame:
        rows = []  # Liste pour stocker les lignes avant de créer le DataFrame

        # Assurez-vous que 'Groupe_Valorise' est une liste pour un traitement cohérent
        donnees_valorisation = data_dict['Donnees_Valorisation']
        #groupe_valorise = groupe_valorise if isinstance(groupe_valorise, list) else [groupe_valorise]
        #pretty.pprint(donnees_valorisation)
        # Pour chaque élément dans 'Groupe_Valorise'
        exclude = ['Groupe_Valorise', 'Donnees_PRM', 'Releve']
        for dv in donnees_valorisation:
            donnees_prm = dv['Donnees_PRM']
            for gv in dv['Groupe_Valorise']:
                for ev in gv['Element_Valorise']:
                    #print(ev)
                    row = donnees_prm | ev | data_dict['Rappel_En_Tete'] | {k:v for k, v in dv.items() if k not in exclude}
                    row['Nature_EV'] = gv['Nature_EV']
                    
                    if 'Releve' in dv:
                        row['Nb_Releve'] = len(dv['Releve'])
                        for i, r in enumerate(dv['Releve']):
                            row[f'Id_Releve_{i}'] = r['Id_Releve']

                    rows.append(row)  # Ajoutez la ligne à la liste des lignes

        return pd.DataFrame(rows)  # Créez et retournez le DataFrame à partir de la liste des lignes
       
    def _spec_post_process(self, df: DataFrame, start_date, end_date) -> DataFrame:
        # Filtrer les résultats par les dates de début et de fin
        filtered_df = df[
            (df['Date_Debut'] <= end_date) & 
            (df['Date_Fin'] >= start_date)
        ]
            
        to_rename = {'Id_PRM' : 'pdl'}
        renamed_df = filtered_df.rename(columns=to_rename)
            
        return renamed_df.sort_values(by=['pdl', 'Date_Facture', 'Id_EV'])