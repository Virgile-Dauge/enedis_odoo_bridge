
import pandas as pd
from pandas import Timestamp, DataFrame

from enedis_odoo_bridge.consumption_estimators import BaseEstimator

class ConcreteEstimator(BaseEstimator):
    def estimate_consumption():
        ...
    def get_estimator_name():
        ...

def test_initialize_dates():
    # Define input data
    meta = DataFrame({'pdl': ['PDL1', 'PDL2', 'PDL3', 'PDL4'], 
                      'Date_Releve': [Timestamp('2021-01-01'), Timestamp('2021-01-04'), Timestamp('2021-01-15'), Timestamp('2021-01-02')], 
                      'Motif_Releve': ['CFNE', 'MES', 'CYCL', 'CFNS']})
    start = Timestamp('2021-01-01')
    end = Timestamp('2021-01-30')

    # Define expected output
    expected_output = DataFrame({'pdl': ['PDL1', 'PDL2', 'PDL3', 'PDL4'],
                                 'start_date': [Timestamp('2021-01-01'), Timestamp('2021-01-04'), Timestamp('2021-01-01'), Timestamp('2021-01-01')], 
                                 'end_date': [Timestamp('2021-01-30'), Timestamp('2021-01-30'), Timestamp('2021-01-30'), Timestamp('2021-01-02')],
                                 'normal_days': [30, 30, 30, 30], 
                                 'actual_days': [30, 27, 30, 2], 
                                 'update_dates': [False, True, False, True]})

    # Instantiate the estimator
    estimator = ConcreteEstimator()

    # Call the method under test
    output = estimator.initialize_dates(meta, start, end)
    #print(expected_output, output)
    # Verify the output
    pd.testing.assert_frame_equal(output, expected_output)