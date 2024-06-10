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
    
