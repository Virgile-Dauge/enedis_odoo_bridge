import pandas as pd
from pathlib import Path
from datetime import date
from typing import Union, Any
from pandas import DataFrame, Series

from enedis_odoo_bridge.enedis_flux_engine.flux_repository import BaseFluxRepository

import pandas as pd
from pandas import DataFrame
from pathlib import Path
from typing import List, Any, Optional
from datetime import date, timedelta

from .base_flux_repository import BaseFluxRepository

class R15FluxRepository(BaseFluxRepository):
    def __init__(self, path: Path):
        # Initialisation du schéma XSD spécifique au flux
        super().__init__(path=path.expanduser() / 'F15', xsd_path=Path(__file__).parent / 'schemas/GRD.XSD.0299.Flux_F15_Donnees_Detail_v3.3.2.xsd')

    def _select_zips(self, start_date, end_date=None) -> List[Path]:
        zip_files =list(self.path.glob("*.zip"))

        horodate : list[date] = [pd.to_datetime(zip_file.stem.split('_')[-1], format='%Y%m%d%H%M%S').date() for zip_file in zip_files]
        if end_date is None:
            print([z for z, h in zip(zip_files, horodate) if (h-start_date).days == 1 or (h-start_date).days == 2])
            return [z for z, h in zip(zip_files, horodate) if (h-start_date).days == 1 or (h-start_date).days == 2]

        return [z for z, h in zip(zip_files, horodate) if (h-start_date).days >= 2 and (h-end_date).days <= 2]

    def _filter_files(self, filenames: List[str]) -> List[str]:
        # Implémentez la logique spécifique pour filtrer les fichiers XML d'intérêt
        return filenames

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
