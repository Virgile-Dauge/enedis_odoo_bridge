import logging
from abc import ABC, abstractmethod
from enedis_odoo_bridge.OdooAPI import OdooAPI
from enedis_odoo_bridge.EnedisFluxEngine import EnedisFluxEngine
    
class BaseProcess(ABC):
    def __init__(self, config: dict[str, str], enedis: EnedisFluxEngine, odoo: OdooAPI):
        self.config = config
        self.enedis = enedis
        self.odoo = odoo
        self.will_update_production_db  = True

    @abstractmethod
    def run(self):
        pass

    # Méthodes communes ici
    def common_method(self):
        # Implémentation de la méthode commune
        pass