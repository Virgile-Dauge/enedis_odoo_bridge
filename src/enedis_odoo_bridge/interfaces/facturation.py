import marimo

__generated_with = "0.7.1"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
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
        start_date_picker,
    )


@app.cell
def __(env, mo):
    mo.md(f"""
          # Données d'entrée : Flux Enedis
          Source ftp : {env['FTP_ADDRESS']} 
          """)
    return


@app.cell
def __(end_date_picker, start_date_picker):
    from enedis_odoo_bridge.enedis_flux_engine import get_r15_by_date
    from pathlib import Path
    flux_path = Path('~/data/flux_enedis/')
    r15 = get_r15_by_date(flux_path, start_date_picker.value, end_date_picker.value)
    return Path, flux_path, get_r15_by_date, r15


@app.cell
def __(r15):
    from enedis_odoo_bridge.enedis_flux_engine  import get_meta_from_r15
    meta = get_meta_from_r15(r15)
    return get_meta_from_r15, meta


@app.cell
def __(r15):
    from enedis_odoo_bridge.enedis_flux_engine import get_CF_from_r15

    cfne, cfns = get_CF_from_r15(r15)
    return cfne, cfns, get_CF_from_r15


@app.cell
def __(mo):
    mo.md(r"### R15")
    return


@app.cell(hide_code=True)
def __(cfne, cfns, meta, mo):
    mo.accordion({"Metadonnées": meta,
                  "Changements de fournisseur entrants": cfne,
                  "Changements de fournisseur sortants": cfns
                 })
    return


@app.cell
def __(mo):
    mo.md(r"### R151")
    return


@app.cell
def __(end_date_picker, flux_path, mo, start_date_picker):
    from enedis_odoo_bridge.enedis_flux_engine import get_r151_by_date
    from enedis_odoo_bridge.utils import get_consumption_names

    _unused = ['zip_file', 'Id_Affaire']
    r151_start = get_r151_by_date(flux_path, start_date_picker.value).drop(columns=_unused)
    r151_end = get_r151_by_date(flux_path, end_date_picker.value).drop(columns=_unused)

    _conso_cols = [c for c in get_consumption_names() if c in r151_start]
    r151_start[_conso_cols] = (r151_start[_conso_cols] / 1000).round()
    _conso_cols = [c for c in get_consumption_names() if c in r151_start]
    r151_end[_conso_cols] = (r151_end[_conso_cols] / 1000).round()

    mo.accordion({f"Index du {start_date_picker.value}": r151_start,
                  f"Index du {end_date_picker.value}": r151_end
    })
    return get_consumption_names, get_r151_by_date, r151_end, r151_start


@app.cell
def __(mo):
    mo.md(
        r"""
        ## Fusion des données 
        On va maintenant combiner les données issues du R15, `cfne` et `cfns`, avec les données issues du R151, `start_index` et `end_index`

        S'il y a eu un $CFNE$ pour un $PDL$, on va remplacer les index du R151 (`start_index`) par celles du relevé de `cfne`

        S'il y a eu un $CFNS$ pour un $PDL$, on va remplacer les index du R151 (`end_index`) par celles du relevé de `cfns`

        On obtient ainsi deux tableaux, l'un avec les index du début de la période, l'autre avec l'index de la fin, qu'ils proviennent du R15 ou du R151.
        """
    )
    return


@app.cell
def __(cfne, cfns, r151_end, r151_start):
    start_index = cfne.set_index('pdl').combine_first(r151_start.set_index('pdl'))
    end_index = cfns.set_index('pdl').combine_first(r151_end.set_index('pdl'))
    return end_index, start_index


@app.cell
def __(end_index, get_consumption_names, start_index):
    import pandas as pd
    # Trouver les PDLs communs
    _pdls_communs = start_index.index.intersection(end_index.index)

    # Calculer la différence pour les colonnes spécifiées
    consos = end_index.loc[_pdls_communs, get_consumption_names()] - start_index.loc[_pdls_communs, get_consumption_names()]
    consos['start_date'] = start_index.loc[_pdls_communs, 'Date_Releve']
    consos['end_date'] = end_index.loc[_pdls_communs, 'Date_Releve']
    # Convertir les colonnes de dates en objets datetime
    consos['start_date'] = pd.to_datetime(consos['start_date'])
    consos['end_date'] = pd.to_datetime(consos['end_date'])

    # Calculer la différence en jours et ajouter 1 pour inclure les deux dates
    consos['j'] = (consos['end_date'] - consos['start_date']).dt.days + 1
    consos.dropna(axis=1, how='all')
    return consos, pd


@app.cell
def __(env, mo):
    mo.md(f"""
          # ODOO

          Site : [{env['ODOO_URL']}]({env['ODOO_URL']})
          """)
    return


@app.cell
def __(mo):
    mo.md(r"## Lancer le cycle de facturation")
    return


@app.cell
def __(env, mo):
    mo.md(
        f"""
        ## Récupération des Abonnements à facturer

        On va chercher tous les abonnements en cours, dont le statut de facturation est _Facture brouillon créée_ ([voir vue kanban]({env['ODOO_URL']}web#action=437&model=sale.order&view_type=kanban))
        """
    )
    return


@app.cell
def __(env):
    from enedis_odoo_bridge.OdooAPI import OdooAPI

    odoo = OdooAPI(config=env, sim=True)
    draft_orders = odoo.search_read('sale.order', filters=[[['state', '=', 'sale'], ['x_invoicing_state', '=', 'draft']]], fields=['id', 'x_pdl', 'invoice_ids', 'x_lisse', 'x_puissance_souscrite']).set_index('x_pdl')

    draft_orders['url'] = draft_orders['sale.order_id'].apply(
        lambda x: f'https://energie-de-nantes.odoo.com/web#id={x}&model=sale.order&view_type=form'
    )
    draft_orders.sort_values(by='sale.order_id')
    return OdooAPI, draft_orders, odoo


@app.cell
def __(mo):
    mo.md(r"## Récupération des factures brouillon des abonnements à facturer")
    return


@app.cell
def __(draft_orders, odoo):
    draft_orders['invoice_ids'] = draft_orders['invoice_ids'].apply(lambda x: max(x) if x else None)
    draft_orders.rename(columns={'sale.order_id': 'order_id', 'invoice_ids': 'move_id'}, inplace=True)

    draft_invoices = odoo.read('account.move', ids=draft_orders['move_id'].to_list(), fields=['invoice_line_ids',])
    draft_orders['invoice_line_ids'] = draft_invoices['invoice_line_ids']

    odoo_data = odoo.add_cat_fields(draft_orders, [])
    return draft_invoices, odoo_data


@app.cell
def __(consos, draft_orders, meta):
    # Fusionner draft_orders et meta en utilisant un left join
    merged_df = draft_orders.merge(meta, how='left', left_index=True, right_index=True)

    # Fusionner le résultat précédent avec consos en utilisant un left join
    merged_df = merged_df.merge(consos, how='left', left_index=True, right_index=True)
    merged_df
    return merged_df,


@app.cell
def __(end_date_picker, merged_df, odoo, start_date_picker):
    merged_df['not_enough_data'] = False
    merged_df.rename(columns={'sale.order_id': 'order_id'}, inplace=True)
    merged_df['move_id'] = False
    print(merged_df)
    odoo.update_draft_invoices(merged_df, start_date_picker.value, end_date_picker.value)
    return


if __name__ == "__main__":
    app.run()
