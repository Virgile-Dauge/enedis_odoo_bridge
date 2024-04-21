from enedis_odoo_bridge.flux_transformers import BaseFluxTransformer, R15FluxTransformer
from pathlib import Path

class FluxTransformerFactory:
    def get_transformer(self, flux_type:str, xsd_path: Path)->BaseFluxTransformer:
        if flux_type == 'R15':
            return R15FluxTransformer(xsd_path)
        #elif flux_type == 'F15':
        #    return F15FluxTransformer(xsd_path)
        #elif flux_type == 'C15':
        #    return C15FluxTransformer(xsd_path)
        else:
            raise ValueError(f"Unsupported Flux type : {flux_type}")