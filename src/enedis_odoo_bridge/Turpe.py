import os
from dotenv import load_dotenv
from rich.pretty import pretty_repr
import pandas as pd
import logging
_logger = logging.getLogger(__name__)

class Turpe:
    """
    A class for computing Turpe values.
    """
    def __init__(self):
        load_dotenv()
        self.constants = {k: float(v) for k, v in os.environ.items() if k.startswith('TURPE_')}

        required = ['TURPE_TAUX_HPH_CU4', 'TURPE_TAUX_HCH_CU4', 
                    'TURPE_TAUX_HPB_CU4', 'TURPE_TAUX_HCB_CU4', 
                    'TURPE_B_CU4', 'TURPE_CG', 'TURPE_CC']
        print(self.constants)
        if not all(c in self.constants for c in required):
            raise OSError(f'Required constants {required} not found in .env file')
        
        _logger.info(f'Turpe constants from .env : {pretty_repr(self.constants)}')

    def compute(self, releves: pd.DataFrame) -> pd.DataFrame:
        required = ['HPH_conso', 'HCH_conso', 'HPB_conso', 'HCB_conso', 'puissance_souscrite']
        if not all(c in releves.columns for c in required):
            raise ValueError(f'Required data {required} not found in imput releves')
        
        releves['turpe'] = sum([
            releves['HPH_conso'].astype(float)*self.constants['TURPE_TAUX_HPH_CU4']*0.01,
            releves['HCH_conso'].astype(float)*self.constants['TURPE_TAUX_HCH_CU4']*0.01,
            releves['HPB_conso'].astype(float)*self.constants['TURPE_TAUX_HPB_CU4']*0.01,
            releves['HCB_conso'].astype(float)*self.constants['TURPE_TAUX_HCB_CU4']*0.01,
            sum([releves['puissance_souscrite'].astype(float) * self.constants['TURPE_B_CU4'],
                self.constants['TURPE_CG'],
                self.constants['TURPE_CC']])/12])
        return releves