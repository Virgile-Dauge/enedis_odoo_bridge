from pathlib import Path

from .base_flux_repository import BaseFluxRepository
from .r151_flux_repository import R151FluxRepository

class FluxRepositoryFactory:
    def get_flux_repository(self, flux_type:str, root_path: Path=Path('~/data/flux_enedis'))->BaseFluxRepository:
        if flux_type == 'R151':
            return R151FluxRepository(root_path)
        #elif flux_type == 'F15':
        #    return F15FluxTransformer()
        #elif flux_type == 'R151':
        #    return R151FluxRepository(root_path)
        #elif flux_type == 'C15':
        #    return C15FluxTransformer()
        else:
            raise ValueError(f"Unsupported Flux type : {flux_type}")