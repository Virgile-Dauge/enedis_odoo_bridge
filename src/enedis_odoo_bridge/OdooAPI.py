from dotenv import load_dotenv
import os
import xmlrpc.client
from xmlrpc.client import MultiCall

from pathlib import Path
from typing import Dict, List

import logging
_logger = logging.getLogger(__name__)

class OdooAPI:
    def __init__(self):
        load_dotenv()

        self.url = os.getenv("URL")
        self.db = os.getenv("DB")
        self.username = os.getenv("USERNAME")
        self.password = os.getenv("PASSWORD")

        with xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common') as common:
            #common.version()
            self.uid = common.authenticate(self.db, self.username, self.password, {})

        self.proxy = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        # Récup des logs des appels de scripts précédents
        
        logs = self.execute('x_log_enedis', 'search_read', [[]], {'fields': ['x_name']})
        self.log_history = [Path(l['x_name']).stem for l in logs]
        _logger.info(f'{len(self.log_history)} x_log_enedis found in Odoo db.')

    def execute(self, model: str, method: str, *args, **kwargs) -> List:
        res = self.proxy.execute_kw(self.db, self.uid, self.password, model, method, *args, **kwargs)
        return res if isinstance(res, list) else [res]
    
    def get_drafts(self)-> List[Dict]:
        drafts = self.execute('account.move', 'search_read', 
        [[['move_type', '=', 'out_invoice'], ['state', '=', 'draft'], ['x_order_id','!=',False]]], 
        {'fields': ['invoice_line_ids', 'date', 'x_order_id', 'x_turpe']})

        # Récupération des PDL
        bons = self.execute('sale.order', 'read', 
                            [[d['x_order_id'][0] for d in drafts]], 
                            {'fields': ['x_pdl']})

        _logger.info(f'{len(drafts)} drafts invoices found.')
        _logger.info(drafts)

        # On ajoute le PDL à chaque facture d'énergie
        return [d|{'pdl': p['x_pdl']} for d, p in zip(drafts, bons)] #if len(b['x_pdl'])==14
    
    def write(self, model: str, log: Dict[str, str])-> List[int]:
        """
        Writes a log entry in the Odoo database.

        Args:
            log (Dict[str, str]): A dictionary containing the log entry data.

        Returns:
            int: The ID of the newly created log entry in the Odoo database.

        """
        id = self.execute(model, 'create', [log])
        if not isinstance(id, list):
            id = [int(id)]
        _logger.info(f'{model} #{id} writen in Odoo db.')
        return id

        

