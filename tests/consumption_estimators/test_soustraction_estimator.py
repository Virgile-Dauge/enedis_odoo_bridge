import pandas as pd
from pandas import Timestamp
from enedis_odoo_bridge.consumption_estimators import SoustractionEstimator

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

