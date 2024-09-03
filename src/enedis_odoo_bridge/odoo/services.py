from ..OdooAPI import OdooAPI
import pandas as pd
from pandas import DataFrame

def get_valid_subscriptions_pdl(config: dict) -> DataFrame:
    # Initialiser OdooAPI avec le dict de configuration
    odoo_api = OdooAPI(config=config, sim=True)
    
    # Lire les abonnements Odoo valides en utilisant la fonction search_read
    valid_subscriptions = odoo_api.search_read('sale.order', 
                                               filters=[[['is_subscription', '=', True], 
                                                        ['is_expired', '=', False], 
                                                        ['state', '=', 'sale'], 
                                                        ['subscription_state', '=', '3_progress']]], 
                                               fields=['x_pdl', 'x_lisse'])
    
    
    return valid_subscriptions.rename(columns={'x_pdl': 'pdl', 'x_lisse': 'lisse'})

def get_pdls(config: dict) -> DataFrame:
    # Initialiser OdooAPI avec le dict de configuration
    odoo_api = OdooAPI(config=config, sim=True)
    
    # Lire les abonnements Odoo valides et passés en utilisant la fonction search_read
    all_subscriptions = odoo_api.search_read('sale.order', 
                                               filters=[[['is_subscription', '=', True],
                                                        ['state', '=', 'sale'], ]], 
                                               fields=['x_pdl'])
    
    
    return all_subscriptions.rename(columns={'x_pdl': 'pdl',})


