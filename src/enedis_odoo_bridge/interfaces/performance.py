import marimo

__generated_with = "0.8.4"
app = marimo.App(width="medium")


@app.cell
def __():
    import cProfile
    import marimo as mo
    import pandas as pd
    import numpy as np
    from datetime import date
    from pathlib import Path

    from enedis_odoo_bridge.utils import gen_dates
    from enedis_odoo_bridge.utils import load_prefixed_dotenv

    env = load_prefixed_dotenv(prefix='ENEDIS_ODOO_BRIDGE_')
    flux_path = Path('~/data/flux_enedis/')
    default_start, default_end = gen_dates()
    start_date_picker = mo.ui.date(value=default_start)
    end_date_picker = mo.ui.date(value=default_end)

    from enedis_odoo_bridge.enedis_flux_engine import get_f15_by_date

    return (
        Path,
        cProfile,
        date,
        default_end,
        default_start,
        end_date_picker,
        env,
        flux_path,
        gen_dates,
        get_f15_by_date,
        load_prefixed_dotenv,
        mo,
        np,
        pd,
        start_date_picker,
    )


@app.cell
def __(cProfile):
    cProfile.run('get_f15_by_date(flux_path, start_date_picker.value, end_date_picker.value)')
    return


if __name__ == "__main__":
    app.run()
