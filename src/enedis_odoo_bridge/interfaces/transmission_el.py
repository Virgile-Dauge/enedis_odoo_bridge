import marimo

__generated_with = "0.8.4"
app = marimo.App(width="medium")


@app.cell
def __(mo):
    mo.md(
        r"""
        # Transmission des données de facturation à EL

        Ici, les flux sont automatiquement téléchargés, puis on récupère le f15, et on y enleve tous les éléments d'EDN.
        """
    )
    return


@app.cell
async def __():
    from download import app
    # execute the notebook
    result = await app.embed()
    result.output
    return app, result


@app.cell(hide_code=True)
def __():
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
    mo.md(
        f"""
        ## Paramétrage des flux
        Choisis la date de début {start_date_picker} et de fin {end_date_picker}\n
        """
    )
    return (
        Path,
        date,
        default_end,
        default_start,
        end_date_picker,
        env,
        flux_path,
        gen_dates,
        load_prefixed_dotenv,
        mo,
        np,
        pd,
        start_date_picker,
    )


@app.cell
def __(env):
    from enedis_odoo_bridge.odoo import get_pdls
    _abonnements = get_pdls(env)
    pdls_edn = set(_abonnements['pdl'])
    return get_pdls, pdls_edn


@app.cell(hide_code=True)
def __(end_date_picker, flux_path, mo, pd, start_date_picker):
    from enedis_odoo_bridge.enedis_flux_engine import get_f15_by_date
    f15 = get_f15_by_date(flux_path, start_date_picker.value, end_date_picker.value)

    f15['start_date'] = start_date_picker.value
    f15['start_date'] = pd.to_datetime(f15['start_date']).dt.date

    f15['end_date'] = end_date_picker.value
    f15['end_date'] = pd.to_datetime(f15['end_date']).dt.date

    f15 = f15[f15['Date_Facture'] >= f15['start_date']]
    f15 = f15[f15['Date_Facture'] <= f15['end_date']]
    f15 = f15.drop(columns=['start_date', 'end_date'])

    mo.accordion({'F15 complet sur la période' : f15})
    return f15, get_f15_by_date


@app.cell
def __(mo):
    mo.md(r"""## F15 sans les pdl EDN""")
    return


@app.cell(hide_code=True)
def __(f15, pdls_edn):
    f15_el = f15[~f15['pdl'].isin(pdls_edn)]
    f15_el
    return f15_el,


@app.cell
def __(mo):
    mo.md(
        r"""
        ## Édition de la facture 

        Ici, on regroupe et on somme le `Montant_HT` de l'ensemble des lignes qui ont le même `Taux_TVA_Applicable`.
        Chacune de ses lignes sera une ligne de facture, la somme étant le coût unitaire, il faudra bien ajouter la taxe correspondante (Par ex 20%S)
        """
    )
    return


@app.cell
def __(f15_el):
    f15_el_next = f15_el
    f15_el_next = f15_el_next[["Montant_HT", "Taux_TVA_Applicable"]]
    f15_el_next = f15_el_next.groupby(["Taux_TVA_Applicable"], dropna=True).sum()
    f15_el_next
    return f15_el_next,


if __name__ == "__main__":
    app.run()
