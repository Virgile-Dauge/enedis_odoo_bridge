from pathlib import Path
from enedis_odoo_bridge.enedis_flux_engine.zip_repository import BaseZipRepository
from typing import Any
import pandas as pd
from pandas import DataFrame
import xmlschema
from rich.pretty import pprint
from rich import inspect

class C15ZipRepository(BaseZipRepository):
    def xml_to_dict(self, xml_path: Path) -> dict[str, Any]:
        xsd_path = Path(__file__).parent / 'schemas/GRD.XSD.0301.Flux_C15_v4.1.1.xsd'
        # validation='lax' pck le fichier xml n'est pas valide :
        # Reason: Unexpected child with tag 'Borne_Fixe' at position 14. Tag 'Refus_Pose_AMM' expected.
        # Cela renvoie un tuple(dict(données extraites), liste(erreurs)) 
        return xmlschema.XMLSchema(xsd_path).to_dict(xml_path, validation='lax')[0]

    
    def dict_to_dataframe(self, data_dict: dict[str, Any]) -> DataFrame:
        # PRM
        ## Id_PRM
        ## Num_Depannage
        ## Jour_Fixe_Releve
        ## Periodicite_Releve
        ## Adresse_Installation
        ## Situation_Contractuelle
        ### Etat_Contractuel
        ### Structure_Tarifaire
        #### Formule_Tarifaire_Acheminement
        #### Puissance_Souscrite
        rows : list[dict[str, Any]] = []
        creation_date = data_dict['En_Tete_Flux']['Date_Creation']
        for prm in data_dict['PRM']:
            row = {
                'Id_PRM': prm.get('Id_PRM'),
                'Date': creation_date,
                'Num_Depannage': prm.get('Num_Depannage'),
                'Jour_Fixe_Releve': prm.get('Jour_Fixe_Releve'),
                'Periodicite_Releve': prm.get('Periodicite_Releve'),
                #'Adresse_Installation': prm.get('Adresse_Installation'),
                #'Etat_Contractuel': prm.get('Situation_Contractuelle', {}).get('Etat_Contractuel'),
                'Formule_Tarifaire_Acheminement': prm.get('Situation_Contractuelle', {}).get('Structure_Tarifaire', {}).get('Formule_Tarifaire_Acheminement'),
                'Puissance_Souscrite': prm.get('Situation_Contractuelle', {}).get('Structure_Tarifaire', {}).get('Puissance_Souscrite')
            }
            rows.append(row)
        

        return pd.DataFrame(rows)  # Créez et retournez le DataFrame à partir de la liste des lignes
    
    def preprocess(self) -> DataFrame:
                # Convert columns where the last level of the index starts with "Date_" to datetime
        for col in self.data.columns:
            if col.startswith("Date_"):
                self.data[col] = pd.to_datetime(self.data[col]).dt.tz_localize('Etc/GMT-2')
        self.data = self.data.rename(columns={'Id_PRM': 'pdl'})
        return self.data.reset_index(drop=True).sort_values(['pdl'])#.set_index(['pdl', 'Id_EV'])
    
