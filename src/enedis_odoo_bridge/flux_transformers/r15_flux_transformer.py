from enedis_odoo_bridge.flux_transformers import BaseFluxTransformer
from typing import Any
import pandas as pd
from pandas import DataFrame

class R15FluxTransformer(BaseFluxTransformer):
    def dict_to_dataframe(self, data_dict: dict[str, Any]):
        # Initialize an empty list to hold all rows before creating the DataFrame
        rows = []

        # Iterate through each PRM
        for prm in data_dict['PRM']:
            id_prm = prm['Id_PRM']  # Extract the Id_PRM

            # Ensure 'Donnees_Releve' is a list for consistent processing
            donnees_releve = prm['Donnees_Releve'] if isinstance(prm['Donnees_Releve'], list) else [prm['Donnees_Releve']]

            # Iterate through each 'Donnees_Releve'
            for dr in donnees_releve:
                row = {'.meta.pdl': id_prm}  # Start a new row with Id_PRM
                meta = {'.meta.'+k: v for k, v in dr.items() if k != 'Classe_Temporelle_Distributeur' and k != 'Classe_Temporelle'}
                row.update(meta)  # Add other variables from 'Donnees_Releve'
                classe_mesure = {'1': 'index', '2': 'conso'}
                # Flatten 'Classe_Temporelle_Distributeur' into columns
                if 'Classe_Temporelle_Distributeur' in dr:
                    for ctd in dr['Classe_Temporelle_Distributeur']:
                        # Assuming 'Id_Classe_Temporelle' is unique within each 'Donnees_Releve'
                        for key, value in ctd.items():
                            column_name = f"{classe_mesure[ctd['Classe_Mesure']]}.{ctd['Id_Classe_Temporelle']}.{key}"
                            row[column_name] = value
                elif 'Classe_Temporelle' in dr:
                    for ctd in dr['Classe_Temporelle']:
                        # Assuming 'Id_Classe_Temporelle' is unique within each 'Donnees_Releve'
                        for key, value in ctd.items():
                            column_name = f"{classe_mesure[ctd['Classe_Mesure']]}.{ctd['Id_Classe_Temporelle']}.{key}"
                            row[column_name] = value

                rows.append(row)
        df = DataFrame(rows)
        columns = [tuple(k.split('.')) for k in df.columns]
        #if len(columns) != len(df.columns):
        print(columns, df.columns)
        column_renaming = {
            # Add more columns to rename here
            # 'some_old_column_name': 'new_column_name',
        }
        df = df.rename(column_renaming)
        # Create a MultiIndex for the columns
        multi_index_columns = pd.MultiIndex.from_tuples(columns)
        # Assign the MultiIndex to your DataFrame's columns
        df.columns = multi_index_columns
        print(columns, df.columns)
        return df
    
    def preprocess(self) -> DataFrame:
        self.data = self.data.sort_values(by=[('', 'meta', 'pdl'), ('', 'meta', 'Date_Releve')],)
        self.data = self.data.reset_index(drop=True)

        # TODO : DROP all Id_Classe_Temporelle, all Libelle_Classe_Temporelle Classe_Mesure
        # Identify columns to drop where the lower level of the MultiIndex ends with "Classe_Temporelle"
        to_drop = [col for col in self.data.columns if col[2].endswith("Classe_Temporelle")]
        self.data = self.data.drop(columns=to_drop)
        # TODO : Un seul num série Num_Serie
        return self.data