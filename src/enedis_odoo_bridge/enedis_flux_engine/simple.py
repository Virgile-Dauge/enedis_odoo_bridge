import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path


import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict
def xml_to_dataframe(xml_path: Path, row_level: str, 
                     metadata_fields: dict[str, str] = {}, 
                     data_fields: dict[str, str] = {},
                     nested_fields: list[tuple[str, str, str]] = {}) -> pd.DataFrame:
    """
    Convert an XML structure to a Pandas DataFrame.
    
    Parameters:
    xml_path (Path): Path to the XML file.
    row_level (str): XPath-like string that defines the level in the XML where each row should be created.
    metadata_fields (Dict[str, str]): Dictionary of metadata fields with keys as field names and values as XPath-like strings.
    data_fields (Dict[str, str]): Dictionary of data fields with keys as field names and values as XPath-like strings.
    Returns:
    pd.DataFrame: DataFrame representation of the XML data.
    """
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    root_tag = root.tag
    print(root_tag)

    meta: dict[str, str] = {}
    # Extract metadata fields
    for field_name, field_xpath in metadata_fields.items():
        field_elem =  root.find(field_xpath)
        if field_elem is not None:
            meta[field_name] = field_elem.text

    all_rows = []
    for row in root.findall(row_level):
        # Extract data fields
        row_data = {field_name: row.find(field_xpath)
                    for field_name, field_xpath in data_fields.items()}
        row_data = {k:v.text for k,v in row_data.items() if v is not None}
        nested_data = {}
        for r, k, v in nested_fields:
           for nr in row.findall(r):
               nested_data[nr.find(k).text] = nr.find(v).text   
        
        all_rows.append(row_data | nested_data)
    
    df = pd.DataFrame(all_rows)
    for k, v in meta.items():
        df[k] = v
    return df

def main():

    # Exemple R151
    xml_path = Path('tests/temp_dir/ERDF_R151_17X000001117366M_GRD-F139_108529521_00160_Q_00001_00001_20240912030614.xml')
    row_level = './/PRM'
    metadata_fields = {
        'Unité': 'En_Tete_Flux/Unite_Mesure_Index',
        
    }
    data_fields = {
        'Date_Releve': 'Donnees_Releve/Date_Releve',
        'pdl': 'Id_PRM',
        'Id_Calendrier_Fournisseur': 'Donnees_Releve/Id_Calendrier_Fournisseur',
        'Id_Affaire': 'Donnees_Releve/Id_Affaire'
    }
    nested_fields = [
        ('Donnees_Releve/Classe_Temporelle_Distributeur', 'Id_Classe_Temporelle', 'Valeur'),
    ]
        
    df = xml_to_dataframe(xml_path, row_level, metadata_fields, data_fields, nested_fields)
    print(df)

    df.to_csv('R151.csv', index=False)

    # Exemple R15
    xml_path = Path('tests/temp_dir/17X100A100A0001A_R15_17X000001117366M_GRD-F139_0322_00001_00001_00001.xml')
    row_level = './/PRM'
    metadata_fields = {
        'Unité': 'En_Tete_Flux/Unite_Mesure_Index',
        
    }
    data_fields = {
        'Date_Releve': 'Donnees_Releve/Date_Releve',
        'pdl': 'Id_PRM',
        'Id_Calendrier': 'Donnees_Releve/Id_Calendrier',
        'Ref_Situation_Contractuelle': 'Donnees_Releve/Ref_Situation_Contractuelle',
        'Type_Compteur': 'Donnees_Releve/Type_Compteur',
        'Motif_Releve': 'Donnees_Releve/Motif_Releve',
        'Ref_Demandeur': 'Donnees_Releve/Ref_Demandeur',
        'Id_Affaire': 'Donnees_Releve/Id_Affaire'
    }
    nested_fields = [
        ('Donnees_Releve/Classe_Temporelle_Distributeur', 'Id_Classe_Temporelle', 'Valeur'),
    ]
        
    df = xml_to_dataframe(xml_path, row_level, metadata_fields, data_fields, nested_fields)
    print(df)

    df.to_csv('R15.csv', index=False)

if __name__ == "__main__":
    main()

