from pathlib import Path

from .base_flux_repository import BaseFluxRepository
from .r151_flux_repository import R151FluxRepository
from .r15_flux_repository import R15FluxRepository
from .f15_flux_repository import F15FluxRepository
from .c15_flux_repository import C15FluxRepository

class FluxRepositoryFactory:
    def get_flux_repository(self, flux_type:str, root_path: Path=Path('~/data/flux_enedis'))->BaseFluxRepository:
        if flux_type == 'R151':
            return R151FluxRepository(root_path)
        elif flux_type == 'R15':
            return R15FluxRepository(root_path)
        elif flux_type == 'F15':
            return F15FluxRepository(root_path)
        elif flux_type == 'C15':
            return C15FluxRepository(root_path)
        else:
            raise ValueError(f"Unsupported Flux type : {flux_type}")