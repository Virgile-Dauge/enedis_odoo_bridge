from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd
from datetime import date

class BaseFluxRepository(ABC):
    def __init__(self, root_path: Path) -> None:
        self.root_path = root_path
    @abstractmethod
    def get_flux_by_date(self, start_date: date, end_date: date) -> pd.DataFrame:
        pass
    
    def _preprocess(self, data: pd.DataFrame):
        for col in data.columns:
            if col.startswith("Date_"):
                data[col] = pd.to_datetime(data[col]).dt.date
                
        data = data.reset_index(drop=True)
        return data