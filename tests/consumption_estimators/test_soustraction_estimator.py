import pandas as pd
from pandas import Timestamp
from enedis_odoo_bridge.consumption_estimators import SoustractionEstimator

def test_get_estimator_name():
    # Instantiate the SoustractionEstimator
    estimator = SoustractionEstimator()

    # Expected name
    expected_name = 'Max - Min of available indexes for each temporal class'

    # Call the get_estimator_name method
    actual_name = estimator.get_estimator_name()

    # Assert that the actual name matches the expected name
    assert actual_name == expected_name, "The estimator name does not match the expected value."

def test_estimate_consumption():
    # Setup
    meta = pd.DataFrame({
        'pdl': ['pdl1', 'pdl1', 'pdl2', 'pdl2'],
        'Date_Releve': [Timestamp('2022-01-01'), Timestamp('2022-01-15'), Timestamp('2022-01-01'), Timestamp('2022-01-15')],
        'Statut_Releve': ['INITIAL', 'INITIAL', 'INITIAL', 'INITIAL'],
    })

    index = pd.DataFrame({
        'pdl': ['pdl1', 'pdl1', 'pdl2', 'pdl2'],
        'HPH_Valeur': [100, 200, 300, 400],
        'HPH_Nb_Chiffres_Cadran': [5, 5, 5, 5],
        'HPH_Indicateur_Passage_A_Zero': [0, 0, 0, 0],
        'HPH_Coefficient_Lecture': [1, 1, 1, 1],
    })

    consos = pd.DataFrame()  # Assuming consos is not used in this example

    start = Timestamp('2022-01-01')
    end = Timestamp('2022-01-31')

    estimator = SoustractionEstimator()

    # Exercise
    result = estimator.estimate_consumption(meta, index, consos, start, end)

    # Verify
    expected = pd.DataFrame({
        'pdl': ['pdl1', 'pdl2'],
        'HPH_conso': [100, 100],  # Expected consumption calculation based on the provided logic
    })
    print(expected, result)
    pd.testing.assert_frame_equal(result[['pdl', 'HPH_conso']].reset_index(drop=True), expected.reset_index(drop=True))

def test_estimate_consumption_with_passage_a_zero():
    # Setup
    meta = pd.DataFrame({
        'pdl': ['pdl1', 'pdl1'],
        'Date_Releve': [Timestamp('2022-01-01'), Timestamp('2022-01-15')],
        'Statut_Releve': ['INITIAL', 'INITIAL'],
    })

    index = pd.DataFrame({
        'pdl': ['pdl1', 'pdl1'],
        'HPH_Valeur': [9500, 100],  # Simulate counter rollover
        'HPH_Nb_Chiffres_Cadran': [4, 4],
        'HPH_Indicateur_Passage_A_Zero': [0, 1],  # Indicate counter has rolled over
        'HPH_Coefficient_Lecture': [1, 1],
    })

    consos = pd.DataFrame()  # Assuming consos is not used in this example

    start = Timestamp('2022-01-01')
    end = Timestamp('2022-01-31')

    estimator = SoustractionEstimator()

    # Exercise
    result = estimator.estimate_consumption(meta, index, consos, start, end)

    # Verify
    # Assuming the counter has 10,000 as the max value before rolling over
    expected_consumption = (100 - 9500 + 10**4) * 1  # Expected calculation with rollover
    expected = pd.DataFrame({
        'pdl': ['pdl1'],
        'HPH_conso': [expected_consumption],
    })

    pd.testing.assert_frame_equal(result[['pdl', 'HPH_conso']].reset_index(drop=True), expected.reset_index(drop=True))
    # Additional checks can be added here, such as handling cases with no records, a single record, etc.

def test_estimate_consumption_with_dates():
    # Setup the test data
    meta = pd.DataFrame({
        'Date_Releve': [Timestamp('2022-01-01'), Timestamp('2022-01-10'), Timestamp('2022-01-20')],
        'Statut_Releve': ['INITIAL', 'INITIAL', 'INITIAL'],
        'pdl': ['pdl1', 'pdl1', 'pdl1'],
        'HP_Valeur': [100, 150, 200],
        'HC_Valeur': [50, 75, 100],
        'HP_Nb_Chiffres_Cadran': [0, 0, 0],
        'HC_Nb_Chiffres_Cadran': [0, 0, 0],
        'HP_Indicateur_Passage_A_Zero': [0, 0, 0],
        'HC_Indicateur_Passage_A_Zero': [0, 0, 0],
        'HP_Coefficient_Lecture': [1, 1, 1],
        'HC_Coefficient_Lecture': [1, 1, 1]
    })

    index = meta  # In this test case, index and meta are the same for simplicity
    consos = pd.DataFrame()  # Not used in this implementation
    start = Timestamp('2022-01-01')
    end = Timestamp('2022-01-31')
    
    # Define a dates DataFrame with additional date information
    dates = pd.DataFrame({
        'pdl': ['pdl1'],
        'additional_date_info': [Timestamp('2022-02-01')]
    })

    expected_output = pd.DataFrame({
        'pdl': ['pdl1'],
        'HP_conso': [100],  # 200 - 100 = 100
        'HC_conso': [50],   # 100 - 50 = 50
        'additional_date_info': [Timestamp('2022-02-01')]
    })

    # Instantiate the estimator
    estimator = SoustractionEstimator()

    # Call the method under test with dates
    actual_output = estimator.estimate_consumption(meta, index, consos, start, end, dates)

    # Assert that the actual output matches the expected output, including the merged dates information
    pd.testing.assert_frame_equal(actual_output, expected_output, check_dtype=False)