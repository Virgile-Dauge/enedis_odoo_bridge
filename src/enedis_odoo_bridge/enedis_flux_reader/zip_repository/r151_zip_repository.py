from pathlib import Path
from enedis_odoo_bridge.enedis_flux_reader.zip_repository import BaseZipRepository
from typing import Any
import pandas as pd
from pandas import DataFrame
import xmlschema
from rich.pretty import pprint 

class R151ZipRepository(BaseZipRepository):
    def xml_to_dict(self, xml_path: Path) -> dict[str, Any]:
        xsd_path = Path(__file__).parent / 'schemas/Enedis.SGE.XSD.0315.Flux_R151_v1.2.0.xsd'
        return xmlschema.XMLSchema(xsd_path).to_dict(xml_path)
    def dict_to_dataframe(self, data_dict: dict[str, Any]) -> DataFrame:
        # Initialize an empty list to hold all rows before creating the DataFrame
        rows = []

        # Iterate through each PRM
        for prm in data_dict['PRM']:
            id_prm = prm['Id_PRM']  # Extract the Id_PRM

            # Ensure 'Donnees_Releve' is a list for consistent processing
            donnees_releve = prm['Donnees_Releve'] if isinstance(prm['Donnees_Releve'], list) else [prm['Donnees_Releve']]

            # Iterate through each 'Donnees_Releve'
            for dr in donnees_releve:
                row = {'pdl': id_prm}  # Start a new row with Id_PRM
                meta = {k: v for k, v in dr.items() if k != 'Classe_Temporelle_Distributeur' and k != 'Classe_Temporelle'}
                row.update(meta)  # Add other variables from 'Donnees_Releve'
                # Flatten 'Classe_Temporelle_Distributeur' into columns
                if 'Classe_Temporelle_Distributeur' in dr:
                    for ctd in dr['Classe_Temporelle_Distributeur']:
                        # Assuming 'Id_Classe_Temporelle' is unique within each 'Donnees_Releve'
                        row[ctd['Id_Classe_Temporelle']] = ctd['Valeur']

                #elif 'Classe_Temporelle' in dr:
                #    for ctd in dr['Classe_Temporelle']:
                #        # Assuming 'Id_Classe_Temporelle' is unique within each 'Donnees_Releve'
                #        row[ctd['Id_Classe_Temporelle']] = ctd['Valeur']

                rows.append(row)
        df = DataFrame(rows)

        column_renaming = {
            # Add more columns to rename here
            # 'some_old_column_name': 'new_column_name',
        }
        df = df.rename(column_renaming)
        return df.drop(columns=['Id_Calendrier_Fournisseur', 'Libelle_Calendrier_Fournisseur', 'Id_Calendrier_Distributeur', 'Libelle_Calendrier_Distributeur'])
    
    def preprocess(self) -> DataFrame:
                # Convert columns where the last level of the index starts with "Date_" to datetime
        for col in self.data.columns:
            if col.startswith("Date_"):
                self.data[col] = pd.to_datetime(self.data[col])

        self.data = self.data.sort_values(by=['pdl', 'Date_Releve'],)
        self.data = self.data.reset_index(drop=True)
        return self.data
        

        
    
