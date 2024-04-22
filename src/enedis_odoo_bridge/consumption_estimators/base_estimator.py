from abc import ABC, abstractmethod
import pandas as pd
from pandas import Timestamp, DataFrame
from typing import Dict, List, Any

# Interface commune pour les stratégies
class BaseEstimator(ABC):
    @abstractmethod
    def get_estimator_name(self):
        pass
    @abstractmethod
    def estimate_consumption(self, df: DataFrame, start: Timestamp, end: Timestamp) -> DataFrame:
        pass