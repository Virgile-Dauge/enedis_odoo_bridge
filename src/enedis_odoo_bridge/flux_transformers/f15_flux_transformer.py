import xmlschema
import pandas as pd

from pandas import DataFrame
from typing import Any
from pathlib import Path

from enedis_odoo_bridge.flux_transformers import BaseFluxTransformer

class F15FluxTransformer(BaseFluxTransformer):

    def xml_to_dict(self, xml_path: Path)-> dict[str, Any]:
        if xml_path.stem.endswith('FA.xml'):
            xsd_path = Path('schemas/GRD.XSD.0302.Flux_F15_Donnees_Generales_v3.3.2.xsd')
            return {}
            #return xmlschema.XMLSchema(xsd_path).to_dict(xml_path)

        if 'FL' in xml_path.stem:
            xsd_path = Path('schemas/GRD.XSD.0299.Flux_F15_Donnees_Detail_v3.3.2.xsd')
            return xmlschema.XMLSchema(xsd_path).to_dict(xml_path)

    def dict_to_dataframe(self, data_dict: dict[str, Any]) -> DataFrame:
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
    
    def preprocess(self) -> DataFrame:
                # Convert columns where the last level of the index starts with "Date_" to datetime
        for col in self.data.columns:
            if col.startswith("Date_"):
                self.data[col] = pd.to_datetime(self.data[col]).dt.tz_localize('Etc/GMT-2')
        self.data = self.data.rename(columns={'Id_PRM': 'pdl'})
        return self.data.reset_index(drop=True).sort_values(['pdl', 'Id_EV'])#.set_index(['pdl', 'Id_EV'])

    