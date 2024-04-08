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
    def __init__(self, path):
        load_dotenv()
        self.constants = {k: float(v) for k, v in os.environ.items() if k.startswith('TURPE_')}
        _logger.info(f'Turpe constants from .env : {pretty_repr(self.constants)}')

    def compute(self, releves: pd.DataFrame) -> pd.DataFrame:
        releves['turpe'] = sum([
            releves['HPH_conso'].as_type(float)*self.constants['TURPE_TAUX_HPH_CU4'],
            releves['HCH_conso'].as_type(float)*self.constants['TURPE_TAUX_HCH_CU4'],
            releves['HPB_conso'].as_type(float)*self.constants['TURPE_TAUX_HPB_CU4'],
            releves['HCB_conso'].as_type(float)*self.constants['TURPE_TAUX_HCB_CU4'],
            (releves['P'].as_type(float)+self.constants['TURPE_B_CU4']+self.constants['TURPE_CG']+self.constants['TURPE_CC'])/12])
        return releves