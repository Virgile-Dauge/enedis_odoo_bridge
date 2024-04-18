import xmltodict
import pandas as pd
from pathlib import Path
from typing import Dict, List

from rich.pretty import pretty_repr

from datetime import datetime
from enedis_odoo_bridge import __version__
from enedis_odoo_bridge.utils import unzip
import logging
_logger = logging.getLogger(__name__)

def get_meta(file_path: Path)->Dict: 
    """
    Extracts metadata from the provided file path.

    Parameters:
    file_path (Path): The path to the file from which metadata needs to be extracted.

    Returns:
    Dict: A dictionary containing the metadata extracted from the file.

    Raises:
    ValueError: If the file does not have a '.zip' or '.xml' suffix.

    The function first extracts the metadata from the file path by splitting the file name by underscores. It then checks if the file has a '.zip' or '.xml' suffix. If it does, it constructs a dictionary with the extracted metadata and returns it. If the file does not have a '.zip' or '.xml' suffix, a ValueError is raised.
    """
    meta = file_path.stem.replace('decrypted_', '').split('_')
    type_flux = meta[1]

    if file_path.suffix == '.zip':
        keys = 'emetteur Type destinataire num_contrat Instance_GRD num_seq date'.split()
        y, m, d, h, mm, s = map(int, [meta[6][:4], meta[6][4:6], meta[6][6:8], meta[6][8:10], meta[6][10:12], meta[6][12:]])
        meta[6] = datetime(y, m, d, h, mm, s)
        return {'path': file_path}|dict(zip(keys, meta))
    
    if file_path.suffix == '.xml':
        keys = 'emetteur Type destinataire num_contrat Instance_GRD num_seq XXXXX YYYYY'.split()
        return {'path': file_path}|dict(zip(keys, meta))

    raise ValueError("File must have a '.zip' or '.xml' suffix.")

class R15Parser:
    """
    A class for unziping ZIP and parsing contained XML files from the Enedis R15 Flux.
    """
    def __init__(self, path):

        self.archive_path = Path(path)

        if not self.archive_path.is_file():
            raise FileNotFoundError(f'File {self.archive_path} not found.')
        
        self.name = self.archive_path.stem
        self.meta = get_meta(self.archive_path)
        #self.date = get_meta(self.archive_path)['horodatage']
        self.working_dir = unzip(Path(path))
        # On identifie tous les xml extraits
        self.data = pd.concat([self.parse_one(l) for l in list(self.working_dir.glob('*.xml'))])
        _logger.info(f'{len(self.data)} records extracted from {self.archive_path}')

        
    def parse_one(self, xml_path: Path) -> pd.DataFrame:
        """
        Parses a single XML file from the R15 format and returns a DataFrame.

        Parameters:
        xml_path (Path): The path to the XML file to be parsed.

        Returns:
        pd.DataFrame: A DataFrame containing the parsed data from the XML file.
        """
        with open(xml_path, 'r') as xml:
            prms = xmltodict.parse(xml.read())['R15']['PRM']

        conso_k = ['HPH_conso', 'HCH_conso', 'HPB_conso', 'HCB_conso']
        index_k = ['HPH_index', 'HCH_index', 'HPB_index', 'HCB_index']
        res = []
        if not isinstance(prms, list):
            prms = [prms]
        for p in prms:
            prm = {'pdl': p['Id_PRM']}
            
            # When a single report is available, it is transformed into a list.
            if not isinstance(p['Donnees_Releve'], list):
                p['Donnees_Releve'] = [p['Donnees_Releve']]
            
            for r in p['Donnees_Releve']:
                # When a single Classe_Temporelle is available, it is transformed into a list.
                if 'Classe_Temporelle' in r and not isinstance(r['Classe_Temporelle'], list):
                    r['Classe_Temporelle'] = [r['Classe_Temporelle']]

                # When a single Classe_Temporelle_Distributeur is available, it is transformed into a list.
                if 'Classe_Temporelle_Distributeur' in r and not isinstance(r['Classe_Temporelle_Distributeur'], list):
                    r['Classe_Temporelle_Distributeur'] = [r['Classe_Temporelle_Distributeur']]

                # Data from the report, excluding measurements.
                dr = {k: v for k, v in r.items() if not isinstance(v, list)}

                # Measurements. ATTENTION: Je crois que :
                # - 'Classe_Temporelle_Distributeur' donne 4 classes de conso quoi qu'il arrive,
                # - 'Classe_Temporelle' dépend du contrat client.
                k = 'Classe_Temporelle_Distributeur' if 'Classe_Temporelle_Distributeur' in r else 'Classe_Temporelle'
                for m in r[k]:
                    # Consumption.
                    if m['Classe_Mesure'] == '2':
                        #print({m['Id_Classe_Temporelle'] + '_conso': m['Valeur']})
                        dr[m['Id_Classe_Temporelle'] + '_conso'] = m['Valeur']
                    # Indexes.
                    elif m['Classe_Mesure'] == '1':
                        dr[m['Id_Classe_Temporelle'] + '_index'] = m['Valeur']
                        if 'Valeur_Precedent' in m:
                            dr[m['Id_Classe_Temporelle'] + '_index_p'] = m['Valeur_Precedent']

                # Défini si doit être traité automatiquement
                traitable_automatiquement = all([
                    'HPH_conso' in dr,
                    'HCH_conso' in dr,
                    'HPB_conso' in dr,
                    'HCB_conso' in dr,
                    dr['Statut_Releve'] == 'INITIAL',
                    dr['Motif_Releve'] == 'CYCL',
                    'Motif_Releve_Precedent' in dr and dr['Motif_Releve_Precedent'] in ['CYCL', 'MES', 'CFNE'],
                    ])

                res += [prm | dr | {'traitable_automatiquement': traitable_automatiquement}]
        res_df = pd.DataFrame(res)

        # Conversion vers numériques.
        for k in conso_k+index_k:
            if k in res_df.columns:
                res_df[k] = pd.to_numeric(res_df[k])
        # Conversion des dates.
        dates = ['Date_Releve']
        for k in dates:
            if k in res_df.columns:
                print(res_df[k])
                res_df[k] = pd.to_datetime(res_df[k])
        return res_df
    
    def to_csv(self) -> None:
        self.data.to_csv(self.working_dir.joinpath(self.archive_path.stem+'.csv'), index=False)

    def to_x_log_enedis(self) -> Dict[str, str]:
        # Création d'une entrée de logs pour le modèle x_log_enedis
        return {'x_name': self.name,
            'x_type': self.meta['Type'],
            'x_date': self.meta['date'].isoformat().replace('T',' '),
            'x_script_version': __version__}