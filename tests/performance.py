# python -m cProfile -o output_file.prof performance.py
# snakeviz output_file.prof
import cProfile
import pandas as pd
import numpy as np
from datetime import date
from pathlib import Path

from enedis_odoo_bridge.utils import gen_dates
from enedis_odoo_bridge.utils import load_prefixed_dotenv


env = load_prefixed_dotenv(prefix='ENEDIS_ODOO_BRIDGE_')
flux_path = Path('~/data/flux_enedis/')
default_start, default_end = gen_dates()

# from enedis_odoo_bridge.enedis_flux_engine import get_f15_by_date
# get_f15_by_date(flux_path, default_start, default_end)

from enedis_odoo_bridge.enedis_flux_engine.services import get_f15_by_date_async
get_f15_by_date_async(flux_path, default_start, default_end)

# pd.testing.assert_frame_equal(get_f15_by_date_async(flux_path, default_start, default_end), get_f15_by_date(flux_path, default_start, default_end))