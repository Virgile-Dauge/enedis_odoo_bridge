import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from pandas import Timestamp
from enedis_odoo_bridge.estimators import StrategyMaxMin

def test_strategy_max_min_get_strategy_name():
    # Create an instance of StrategyMaxMin
    strategy = StrategyMaxMin()
    
    # Call the get_strategy_name method
    name = strategy.get_strategy_name()
    
    # Assert that the returned name matches the expected value
    assert name == 'Max - Min of available indexes', "The strategy name should be 'Max - Min of available indexes'"




def test_estimate_consumption():
    # Create an instance of StrategyMaxMin
    strategy = StrategyMaxMin()

    # Mock input data
    data = {
        'R15': pd.DataFrame({
            'pdl': ['pdl1', 'pdl1', 'pdl2', 'pdl2'],
            'Date_Releve': pd.to_datetime(['2023-01-01', '2023-01-31', '2023-01-01', '2023-01-31']),
            'Statut_Releve': ['INITIAL', 'INITIAL', 'INITIAL', 'INITIAL'],
            'HPH_index': [100, 200, 300, 400],
            'HCH_index': [200, 300, 400, 500],
            'HPB_index': [100, 150, 200, 250],
            'HCB_index': [50, 100, 150, 200]
        })
    }

    # Define start and end timestamps
    start = Timestamp('2023-01-01')
    end = Timestamp('2023-01-31')

    # Expected output
    expected = pd.DataFrame({
        'pdl': ['pdl1', 'pdl2'],
        'HPH_conso': [100, 100],
        'HCH_conso': [100, 100],
        'HPB_conso': [50, 50],
        'HCB_conso': [50, 50],
        'start_date': [np.datetime64('2023-01-01'), np.datetime64('2023-01-01')],
        'end_date': [np.datetime64('2023-01-31'), np.datetime64('2023-01-31')]
    }).set_index('pdl')

    # Call the method under test
    result = strategy.estimate_consumption(data, start, end).set_index('pdl')

    # Verify the result
    pd.testing.assert_frame_equal(result, expected)