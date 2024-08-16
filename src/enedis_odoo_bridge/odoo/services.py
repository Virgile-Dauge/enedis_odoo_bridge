from ..OdooAPI import OdooAPI
import pandas as pd

def get_valid_subscriptions_pdl(config: dict) -> list[str]:
    # Initialiser OdooAPI avec le dict de configuration
    odoo_api = OdooAPI(config=config, sim=True)
    
    # Lire les abonnements Odoo valides en utilisant la fonction search_read
    valid_subscriptions = odoo_api.search_read('sale.order', 
                                               filters=[[['is_subscription', '=', True], 
                                                        ['is_expired', '=', False], 
                                                        ['state', '=', 'sale'], 
                                                        ['subscription_state', '=', '3_progress']]], 
                                               fields=['x_pdl'])
    
    
    return list(valid_subscriptions['x_pdl'])




