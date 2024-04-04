from dotenv import load_dotenv
import os
import xmlrpc.client
from xmlrpc.client import MultiCall

from pathlib import Path

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
        
        logs = self.proxy.execute_kw(self.db, self.uid, self.password, 'x_log_enedis', 'search_read', [[]], {'fields': ['x_name']})
        already_done = [Path(l['x_name']).stem for l in logs]
        print(already_done)
