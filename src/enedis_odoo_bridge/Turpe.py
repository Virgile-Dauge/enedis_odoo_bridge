from rich.pretty import pretty_repr
from pandas import DataFrame
import logging

from typing import Dict
from enedis_odoo_bridge.utils import check_required
_logger = logging.getLogger(__name__)

class Turpe:
    """
    A class for computing Turpe values.
    """
    def __init__(self, constants: Dict[str, str]):
        self.constants = check_required(constants, ['TURPE_TAUX_HPH_CU4', 'TURPE_TAUX_HCH_CU4', 
                    'TURPE_TAUX_HPB_CU4', 'TURPE_TAUX_HCB_CU4', 
                    'TURPE_B_CU4', 'TURPE_CG', 'TURPE_CC'])
        
        _logger.info(f'Turpe constants from .env : {pretty_repr(self.constants)}')

    def compute(self, releves: DataFrame) -> DataFrame:
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