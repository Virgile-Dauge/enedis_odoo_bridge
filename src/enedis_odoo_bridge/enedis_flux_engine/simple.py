import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import yaml
import pandas as pd
#import xml.etree.ElementTree as ET
from lxml import etree as ET
from pathlib import Path

import logging

_logger = logging.getLogger(__name__)

def xml_to_dataframe(xml_path: Path, row_level: str, 
                     metadata_fields: dict[str, str] = {}, 
                     data_fields: dict[str, str] = {},
                     nested_fields: list[tuple[str, str, str, str]] = {}) -> pd.DataFrame:
    """
    Convert an XML structure to a Pandas DataFrame.
    
    Parameters:
        xml_path (Path): Path to the XML file.
        row_level (str): XPath-like string that defines the level in the XML where each row should be created.
        metadata_fields (Dict[str, str]): Dictionary of metadata fields with keys as field names and values as XPath-like strings.
        data_fields (Dict[str, str]): Dictionary of data fields with keys as field names and values as XPath-like strings.
        nested_fields: list[tuple[str, str, str, str]]: List of tuples where each tuple contains the prefix field name, the path of elements to find key field name, and value field name.
    Returns:
        pd.DataFrame: DataFrame representation of the XML data.
    """
    
    tree = ET.parse(xml_path)
    root = tree.getroot()
    root_tag = root.tag

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
        for p, r, k, v in nested_fields:
           for nr in row.findall(r):
                key_elem = nr.find(k)
                value_elem = nr.find(v)
                if key_elem is not None and value_elem is not None:
                    nested_data[p + key_elem.text] = value_elem.text
                else:
                    _logger.error(f"Key or value element not found for {r}/{k} or {r}/{v}")   
        
        all_rows.append(row_data | nested_data)
    
    df = pd.DataFrame(all_rows)
    for k, v in meta.items():
        df[k] = v
    return df

def process_xml_files(directory: Path,  
                      row_level: str, 
                      metadata_fields: dict[str, str] = {}, 
                      data_fields: dict[str, str] = {},
                      nested_fields: list[tuple[str, str, str, str]] = {},
                      file_pattern: str | None=None) -> pd.DataFrame:
    all_data = []

    xml_files = [f for f in directory.rglob('*.xml')]

    if file_pattern is not None:
        regex_pattern = re.compile(file_pattern)
        xml_files = [f for f in xml_files if regex_pattern.search(f.name)]
    
    
    _logger.info(f"Found {len(xml_files)} files matching pattern {file_pattern}")
    # Use glob to find all XML files matching the pattern in the directory
    for xml_file in xml_files:
        try:
            df = xml_to_dataframe(xml_file, row_level, metadata_fields, data_fields, nested_fields)
            all_data.append(df)
        except Exception as e:
            _logger.error(f"Error processing {xml_file}: {e}")
    # Combine all dataframes
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()
    
def load_flux_config(flux_type, config_path='flux_configs.yaml'):
    with open(config_path, 'r') as file:
        configs = yaml.safe_load(file)
    
    if flux_type not in configs:
        raise ValueError(f"Unknown flux type: {flux_type}")
    
    return configs[flux_type]

def process_flux(flux_type:str, xml_dir:Path, config_path:Path|None=None):

    if config_path is None:
        # Build the path to the YAML file relative to the script's location
        config_path = Path(__file__).parent / 'simple_flux.yaml'
    config = load_flux_config(flux_type, config_path)
    
    # Convert nested_fields from list of dicts to list of tuples
    nested_fields = [
        (item['prefix'], item['child_path'], item['id_field'], item['value_field'])
        for item in config['nested_fields']
    ]
        # Use a default file_regex if not specified in the config
    file_regex = config.get('file_regex', None)
    df = process_xml_files(
        xml_dir,
        config['row_level'],
        config['metadata_fields'],
        config['data_fields'],
        nested_fields,
        file_regex
    )
    return df
def main():
    import time
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
        ('', 'Donnees_Releve/Classe_Temporelle_Distributeur', 'Id_Classe_Temporelle', 'Valeur'),
    ]
        
    #df = xml_to_dataframe(xml_path, row_level, metadata_fields, data_fields, nested_fields)
    # print(df)

    #df.to_csv('R151.csv', index=False)
    xml_dir = Path('~/data/flux_enedis_expe/R151').expanduser()

    # Add this before the function call
    start_time = time.time()
    df = process_xml_files(xml_dir, 
                           row_level, metadata_fields, data_fields, nested_fields, 
                           )
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time of process_xml_files R151: {execution_time:.2f} seconds")
    print(df)
    # print(list(Path('~/data/flux_enedis_expe/F12').expanduser().rglob('FL_[0-9]*_[0-9]*.xml')))
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
        ('','Donnees_Releve/Classe_Temporelle_Distributeur', 'Id_Classe_Temporelle', 'Valeur'),
    ]
        
    # df = xml_to_dataframe(xml_path, row_level, metadata_fields, data_fields, nested_fields)
    # print(df)
    #df.to_csv('R151.csv', index=False)
    xml_dir = Path('~/data/flux_enedis_expe/R15').expanduser()

    # Add this before the function call
    start_time = time.time()
    df = process_xml_files(xml_dir, 
                           row_level, metadata_fields, data_fields, nested_fields, 
                           )
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time of process_xml_files R15: {execution_time:.2f} seconds")
    print(df)

    # Exemple C15
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
        ('','Donnees_Releve/Classe_Temporelle_Distributeur', 'Id_Classe_Temporelle', 'Valeur'),
    ]
        
    df = xml_to_dataframe(xml_path, row_level, metadata_fields, data_fields, nested_fields)
    # print(df)

    df.to_csv('R15.csv', index=False)

    # Exemple F12
    # Un flux F12 consiste en une archive zip représentant une facture agrégée (pour un contrat GRD-F, une région et un
    # délai de paiement donnés). Cette archive regroupe un ensemble de fichiers XML :
    # un fichier de données générales (présence obligatoire), (FA)
    # un ou plusieurs fichiers de données détaillées (présence obligatoire d’un fichier au minimum), (FL)
    # un fichier de données récapitulatives (présence obligatoire), (FR)
    # un ou plusieurs fichiers de données fiscales (présence obligatoire d’un fichier au minimum) (FL)
    # un fichier de détail de taxes diverses (présence facultative ; réservé pour un usage ultérieur). (FT)
    # Fichier de données générales (FA)
    # Fichier de données détaillées (FL)
    # Fichier de données récapitulatives (FR)
 
    df2 = process_flux('F12', Path('~/data/flux_enedis_expe/F12').expanduser())
    df2.to_csv('F12.csv', index=False)
    # from pandas.testing import assert_frame_equal
    # df_sorted = df.sort_index(axis=1)
    # df2_sorted = df2.sort_index(axis=1)
    # assert_frame_equal(df_sorted, df2_sorted)
    df = process_flux('F15', Path('~/data/flux_enedis_expe/F15').expanduser())
    df.to_csv('F15.csv', index=False)
    print(df)
if __name__ == "__main__":
    main()

