import marimo

__generated_with = "0.7.17"
app = marimo.App(width="medium")


@app.cell
def __(mo):
    mo.md(
        r"""
        # Objectif 

        Produire une facture de résiliation avec régularisation pour les mois déjà facturés et ajouter les trucs pas encore facturés 
        """
    )
    return


@app.cell
def __():
    import marimo as mo
    import pandas as pd
    from datetime import date

    from enedis_odoo_bridge.utils import gen_dates
    from enedis_odoo_bridge.utils import load_prefixed_dotenv

    env = load_prefixed_dotenv(prefix='ENEDIS_ODOO_BRIDGE_')
    default_start, default_end = gen_dates()
    start_date_picker = mo.ui.date(value=default_start)
    end_date_picker = mo.ui.date(value=default_end)
    mo.md(
        f"""
        Choisis la date de début {start_date_picker} et de fin {end_date_picker}
        """
    )

    return (
        date,
        default_end,
        default_start,
        end_date_picker,
        env,
        gen_dates,
        load_prefixed_dotenv,
        mo,
        pd,
        start_date_picker,
    )


@app.cell(hide_code=True)
def __(end_date_picker, env, mo, pd, start_date_picker):
    from pathlib import Path
    flux_path = Path('~/data/flux_enedis/')


    from enedis_odoo_bridge.enedis_flux_engine import get_c15_by_date
    c15 = get_c15_by_date(flux_path, start_date_picker.value, end_date_picker.value)
    c15['Date_Evenement'] = pd.to_datetime(c15['Date_Evenement']).dt.date

    c15['start_date'] = start_date_picker.value
    c15['start_date'] = pd.to_datetime(c15['start_date']).dt.date

    c15['end_date'] = end_date_picker.value
    c15['end_date'] = pd.to_datetime(c15['end_date']).dt.date

    c15_latest = c15.sort_values(by='Date_Evenement', ascending=False).drop_duplicates(subset=['Id_PRM'], keep='first').rename(columns={'Id_PRM':'pdl'}).set_index('pdl')

    c15 = c15[c15['Date_Evenement'] >= c15['start_date']]
    c15 = c15[c15['Date_Evenement'] <= c15['end_date']]
    c15 = c15.drop(columns=['start_date', 'end_date'])

    influx = c15[c15['Nature_Evenement'].isin(['CFNE', 'MES'])].rename(columns={'Id_PRM': 'pdl'}).set_index('pdl')
    outflux = c15[c15['Nature_Evenement'].isin(['CFNS', 'RES'])].rename(columns={'Id_PRM': 'pdl'}).set_index('pdl')

    mo.md(f"""
          # Données d'entrée : Flux Enedis
          Source ftp : {env['FTP_ADDRESS']} 
          """)
    return (
        Path,
        c15,
        c15_latest,
        flux_path,
        get_c15_by_date,
        influx,
        outflux,
    )


@app.cell
def __(mo):
    mo.md(
        r"""
        # Depuis Enedis
        ## Lister les résiliations

        """
    )
    return


@app.cell
def __(mo, outflux):
    table = mo.ui.table(data=outflux.dropna(axis=1, how='all'))
    table
    return table,


@app.cell
def __(mo):
    mo.md(
        r"""
        ## Trouver les MES/CFNE correspondants

        """
    )
    return


@app.cell(hide_code=True)
def __(influx, table):
    import numpy as np

    _lines_in_table = influx.loc[influx.index.isin(table.value.index)]
    _lines_in_table
    return np,


@app.cell
def __(mo):
    mo.md(
        r"""
        ## Calculer le total qu'on doit facturer

        Pour l'abonnement, on compte les jours écoulés **(voir détail lissé pas lissé)**

        Pour les conso, on fait la diff sur la grille turpe entre fin et début (index sont sur les relevés du C15)

        Lister les prestations 
        """
    )
    return


@app.cell
def __(end_date_picker, flux_path, start_date_picker, table):
    from enedis_odoo_bridge.enedis_flux_engine import get_f15_by_date

    _f15 = get_f15_by_date(flux_path, start_date_picker.value, end_date_picker.value)
    prestations = _f15[_f15['Id_PRM'].isin(table.value.index)]
    prestations.dropna(axis=1, how='all')
    return get_f15_by_date, prestations


@app.cell
def __(
    DataFrame,
    c15_latest,
    conso_cols,
    end_date_picker,
    end_index,
    influx,
    merged_data,
    meta,
    np,
    outflux,
    pd,
    start_date_picker,
):
    # Fusionner les données Odoo avec les index de début et de fin issus du R151
    _start_conso_cols = {c: 'start_'+ c for c in conso_cols}
    _end_conso_cols = {c: 'end_'+ c for c in conso_cols}

    merged_data = merged_data.merge(end_index[conso_cols].rename(columns=_end_conso_cols),
                                    how='left',
                                    left_index=True, right_index=True)#, suffixes=('', '_end'))

    merged_data['start_date'] = start_date_picker.value
    merged_data['start_date'] = pd.to_datetime(merged_data['start_date']).dt.date

    merged_data['end_date'] = end_date_picker.value
    merged_data['end_date'] = pd.to_datetime(merged_data['end_date']).dt.date

    # Remplacer les index et les dates de début/fin par les données de changements contractuelles issues du C15
    _start_conso_cols = {c: 'start_'+ c for c in conso_cols} | {'Date_Evenement': 'start_date'}
    _end_conso_cols = {c: 'end_'+ c for c in conso_cols} | {'Date_Evenement': 'end_date'}
    merged_data.update(influx.rename(columns=_start_conso_cols)[_start_conso_cols.values()])
    merged_data.update(outflux.rename(columns=_end_conso_cols)[_end_conso_cols.values()])

    # Calculer la différence entre les index de début et de fin, ainsi que le nombre de jours
    # Calcul de la différence et assignation aux colonnes correspondantes
    _start_cols = ['start_'+c for c in conso_cols]
    _end_cols = ['end_'+c for c in conso_cols]
    for start_col, end_col, conso_col in zip(_start_cols, _end_cols, conso_cols):
        merged_data[conso_col] = merged_data[end_col] - merged_data[start_col]

    merged_data['j'] = (pd.to_datetime(merged_data['end_date']) - pd.to_datetime(merged_data['start_date'])).dt.days + 1

    # On ajoute les métadonnées Type compteur et Num Compteur depuis le R15
    merged_data = merged_data.merge(meta, 
                                    how='left', 
                                    left_index=True, 
                                    right_index=True)

    # On récupère les données de puissance et FTA depuis le C15 `c15_latest`
    merged_data = merged_data.merge(c15_latest[['Formule_Tarifaire_Acheminement', 'Puissance_Souscrite']], 
                                    how='left', 
                                    left_index=True, 
                                    right_index=True)

    def _compute_missing_sums(df: DataFrame) -> DataFrame:
        if 'BASE' not in df.columns:
            df['BASE'] = np.nan  

        df['not_enough_data'] = df[['HPH', 'HPB', 'HCH', 
                'HCB', 'BASE', 'HP',
                'HC']].isna().all(axis=1)
        df['BASE'] = np.where(
                df['not_enough_data'],
                np.nan,
                df[['HPH', 'HPB', 'HCH', 
                'HCB', 'BASE', 'HP', 
                'HC']].sum(axis=1)
            )
        df['HP'] = df[['HPH', 'HPB', 'HP']].sum(axis=1)
        df['HC'] = df[['HCH', 'HCB', 'HC']].sum(axis=1)
        return df
    merged_data = _compute_missing_sums(merged_data)
    merged_data
    return conso_col, end_col, merged_data, start_col


@app.cell
def __(mo):
    mo.md(
        r"""
        # Depuis Odoo

        ## Récupèrer quoiqu'on a facturé
        (POur l'instant les prix n'ont pas changés donc on récup juste les quantités)
        Pour chaque abo, va chercher chacune des factures validées **(check payé pas payé)** et on récup le nb de jours 
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        r"""
        # Régularisation

        Pour chacun des produits (abo, HP, HC, ou Base), on fait la diff `Ce qu'on doit facturer au total` - `ce qu'on a facturé`
        """
    )
    return


if __name__ == "__main__":
    app.run()
