from pathlib import Path
from enedis_odoo_bridge.flux_transformers import BaseFluxTransformer
from typing import Any
import pandas as pd
from pandas import DataFrame
import xmlschema

class R15FluxTransformer(BaseFluxTransformer):
    def xml_to_dict(self, xml_path: Path) -> dict[str, Any]:
        xsd_path = Path('schemas/ENEDIS.SGE.XSD.0293.Flux_R15_v2.3.2.xsd')
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

        column_renaming = {
            # Add more columns to rename here
            # 'some_old_column_name': 'new_column_name',
        }
        df = df.rename(column_renaming)
        # Create a MultiIndex for the columns
        multi_index_columns = pd.MultiIndex.from_tuples(columns)
        # Assign the MultiIndex to your DataFrame's columns
        df.columns = multi_index_columns
        return df
    
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
        num_serie_columns = [col for col in data.columns if col[2] == 'Num_Serie']
        data[('', 'meta', 'Num_Serie')] = data[num_serie_columns].apply(check_num_serie_uniformity, axis=1)
        # Optionally, drop the original 'Num_Serie' columns if they are no longer needed
        return data.drop(columns=num_serie_columns)

    def exact_drop(self, data: DataFrame, keys_to_drop: list[str])-> DataFrame:
        level = data.columns.nlevels-1
        to_drop = [col for col in data.columns if col[level] in keys_to_drop]
        return data.drop(columns=to_drop)
    
    def endswith_drop(self, data: DataFrame, keys_to_drop: list[str])-> DataFrame:
        level = data.columns.nlevels-1
        to_drop = [col for col in self.data.columns if any(col[level].endswith(k) for k in keys_to_drop)]
        return data.drop(columns=to_drop)
    
    def preprocess(self) -> DataFrame:
        self.data = self.data.sort_values(by=[('', 'meta', 'pdl'), ('', 'meta', 'Date_Releve')],)
        self.data = self.data.reset_index(drop=True)

        self.data = self.compress_serial_number(self.data)
        self.data = self.exact_drop(self.data, ['Unite_Mesure',
                                                'Classe_Mesure', 
                                                'Id_Classe_Temporelle',
                                                'Libelle_Classe_Temporelle', ])
        self.data = self.endswith_drop(self.data, ['Classe_Temporelle'])
        
        # Convert columns where the last level of the index starts with "Date_" to datetime
        for col in self.data.columns:
            if col[2].startswith("Date_"):
                self.data[col] = pd.to_datetime(self.data[col])
            # Convert all "index" and "conso" values to float
        for col in self.data.columns:
            if col[0] in ['index', 'conso']:
                self.data[col] = self.data[col].astype(float)
        return self.data
    
    def get_meta(self)-> DataFrame:
        # Select 'meta' level columns and drop the MultiIndex to simplify the DataFrame
        meta_data = self.data.xs('meta', level=1, axis=1, drop_level=True)
        # Simplify the column index to remove the MultiIndex
        #meta_data.columns = meta_data.columns.droplevel(1)
        meta_data.columns = meta_data.columns.droplevel(0)
        return meta_data
    
    def get_consu(self)-> DataFrame:
        # Select 'meta' level columns and drop the MultiIndex to simplify the DataFrame
        conso_data = self.data.xs('conso', level=0, axis=1, drop_level=True).copy()
        # Simplify the column index to remove the MultiIndex
        conso_data.columns = ['_'.join(c) for c in conso_data.columns]
        conso_data['pdl'] = self.data[('', 'meta', 'pdl')]
        return conso_data
    
    def get_index(self)-> DataFrame:
        # Select 'meta' level columns and drop the MultiIndex to simplify the DataFrame
        index_data = self.data.xs('index', level=0, axis=1, drop_level=True).copy()
        # Simplify the column index to remove the MultiIndex
        index_data.columns = ['_'.join(c) for c in index_data.columns]
        index_data['pdl'] = self.data[('', 'meta', 'pdl')]
        return index_data