from enedis_odoo_bridge.flux_transformers import BaseFluxTransformer
from typing import Any
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
                row = {'pdl': id_prm}  # Start a new row with Id_PRM
                row.update({k: v for k, v in dr.items() if k != 'Classe_Temporelle_Distributeur'})  # Add other variables from 'Donnees_Releve'

                # Flatten 'Classe_Temporelle_Distributeur' into columns
                if 'Classe_Temporelle_Distributeur' in dr:
                    for ctd in dr['Classe_Temporelle_Distributeur']:
                        # Assuming 'Id_Classe_Temporelle' is unique within each 'Donnees_Releve'
                        for key, value in ctd.items():
                            column_name = f"{ctd['Id_Classe_Temporelle']}_{key}"
                            row[column_name] = value

                rows.append(row)
        df = DataFrame(rows)
        column_renaming = {
            # Add more columns to rename here
            # 'some_old_column_name': 'new_column_name',
        }
        return df.rename(column_renaming)