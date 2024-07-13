import marimo

__generated_with = "0.7.1"
app = marimo.App(width="medium")


@app.cell
def delimitation_periode():
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
def lecture_flux_r15(end_date_picker, start_date_picker):
    from enedis_odoo_bridge.enedis_flux_engine import get_r15_by_date
    from pathlib import Path
    flux_path = Path('~/data/flux_enedis/')
    r15 = get_r15_by_date(flux_path, start_date_picker.value, end_date_picker.value)
    return Path, flux_path, get_r15_by_date, r15


@app.cell
def extraction_meta_r15(r15):
    from enedis_odoo_bridge.enedis_flux_engine  import get_meta_from_r15
    meta = get_meta_from_r15(r15)
    return get_meta_from_r15, meta


@app.cell
def extraction_cf_r15(r15):
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
def recuperation_index_enedis(
    end_date_picker,
    flux_path,
    mo,
    start_date_picker,
):
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
def fusion_donnees_enedis(
    cfne,
    cfns,
    get_consumption_names,
    r151_end,
    r151_start,
):
    import pandas as pd
    # Combinaison des dates de la période et des éventuels CFNE ou CFNS
    start_index = cfne.set_index('pdl').combine_first(r151_start.set_index('pdl'))
    end_index = cfns.set_index('pdl').combine_first(r151_end.set_index('pdl'))

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
    return consos, end_index, pd, start_index


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


@app.cell(hide_code=True)
def recuperation_abonnements_odoo(env, mo):
    from enedis_odoo_bridge.OdooAPI import OdooAPI

    odoo = OdooAPI(config=env, sim=True)
    _draft_orders_request = odoo.search_read('sale.order', filters=[[['state', '=', 'sale'], ['x_invoicing_state', '=', 'draft']]], fields=['id', 'x_pdl', 'invoice_ids', 'x_lisse', 'x_puissance_souscrite'])

    _stop_msg = mo.callout(mo.md(
        f"""
        ## ⚠ Aucun abonnement à facturer trouvé sur [Odoo]({env['ODOO_URL']}web#action=437&model=sale.order&view_type=kanban). ⚠ 
        Ici ne sont prises en comptes que les cartes dans la colonne **Facture brouillon créée**, et le programme n'en trouve pas.
        Le processus de facturation ne peut pas continuer en l'état. Plusieurs causes possibles : 
        1. Le processus de facturation n'a pas été lancé dans Odoo. Go le lancer. 
        2. Toutes les cartes abonnement ont déjà été déplacées dans une autre colonne. Si tu souhaite néanmoins re-mettre à jour un des abonnements, il suffit de redéplacer sa carte dans la colonne Facture brouillon créée. Attention, ça va écraser les valeurs de sa facture."""), kind='warn')

    mo.stop(_draft_orders_request.empty, _stop_msg)

    draft_orders = _draft_orders_request.set_index('x_pdl').sort_values(by='sale.order_id')
    draft_orders.rename(columns={'sale.order_id': 'order_id', 'invoice_ids': 'move_id'}, inplace=True)
    draft_orders['move_id'] = draft_orders['move_id'].apply(lambda x: max(x) if x else None)

    # draft_orders['url'] = draft_orders['order_id'].apply(
    #     lambda x: f'https://energie-de-nantes.odoo.com/web#id={x}&model=sale.order&view_type=form'
    # )
    #draft_orders.at['14265701793516', 'move_id'] = None
    _to_display = [draft_orders]
    _no_invoices = draft_orders[draft_orders['move_id'].isna()]

    if not _no_invoices.empty:
        draft_orders.dropna(subset=['move_id'], inplace=True)
        _to_display.append(mo.callout("""Les abonnements suivants ont une facture et seront traités :""", kind='success'))
        _to_display.append(_no_invoices)
        _to_display.append(mo.callout("""Les abonnements suivants n'ont pas de facture et ne seront pas traités, il faudra le faire manuellement :""", kind='warn'))
    mo.vstack(reversed(_to_display))
    return OdooAPI, draft_orders, odoo


@app.cell
def __(mo):
    mo.md(r"## Récupération des factures brouillon des abonnements à facturer")
    return


@app.cell
def recuperation_facture_odoo(draft_orders, env, mo, odoo):


    draft_invoices = odoo.read('account.move', ids=draft_orders['move_id'].to_list(), fields=['invoice_line_ids', 'state'])

    _stop_msg = mo.callout(mo.md(
        f"""
        ## ⚠ Aucune facture brouillon trouvée sur [Odoo]({env['ODOO_URL']}web#action=437&model=account.move&view_type=list). ⚠ 
        Ici ne sont prises en comptes que les cartes dans la colonne **Facture brouillon créée**, et le programme n'en trouve pas.
        Le processus de facturation ne peut pas continuer en l'état. Plusieurs causes possibles : 
        1. Le processus de facturation n'a pas été lancé dans Odoo. Go le lancer. 
        2. Toutes les cartes abonnement ont déjà été déplacées dans une autre colonne. Si tu souhaite néanmoins re-mettre à jour un des abonnements, il suffit de redéplacer sa carte dans la colonne Facture brouillon créée. Attention, ça va écraser les valeurs de sa facture."""), kind='warn')

    mo.stop(draft_invoices.empty, _stop_msg)

    #draft_orders['invoice_line_ids'] = draft_invoices['invoice_line_ids']

    # Fusionner les DataFrames sur 'order_id' et assigner le résultat à draft_orders
    # Réinitialiser l'index avant la fusion
    draft_orders.reset_index(inplace=True)
    draft_invoices.reset_index(inplace=True)

    _merged = draft_orders.merge(draft_invoices[['account.move_id', 'invoice_line_ids']], left_on='move_id', right_on='account.move_id', how='left')
    #odoo_data = odoo.add_cat_fields(draft_orders, [])
    draft_orders, draft_invoices, _merged
    _merged.set_index('x_pdl')
    odoo_data = odoo.add_cat_fields(_merged, []).set_index('x_pdl', drop=True)
    odoo_data
    return draft_invoices, odoo_data


@app.cell
def __(mo):
    mo.md(r"# Fusion des données Enedis et Odoo")
    return


@app.cell
def fusion_enedis_odoo(consos, meta, odoo_data):
    # Fusionner draft_orders et meta en utilisant un left join
    merged_df = odoo_data.merge(meta, how='left', left_index=True, right_index=True)

    # Fusionner le résultat précédent avec consos en utilisant un left join
    merged_df = merged_df.merge(consos, how='left', left_index=True, right_index=True)

    merged_df.dropna(axis=1, how='all')
    return merged_df,


@app.cell
def __(end_date_picker, merged_df, odoo, start_date_picker):
    merged_df['not_enough_data'] = False
    merged_df.rename(columns={'sale.order_id': 'order_id'}, inplace=True)
    merged_df['move_id'] = False

    merged_df['turpe_fix'] = 0
    merged_df['turpe_var'] = 0
    print(merged_df)
    odoo.update_draft_invoices(merged_df, start_date_picker.value, end_date_picker.value)
    return


if __name__ == "__main__":
    app.run()
