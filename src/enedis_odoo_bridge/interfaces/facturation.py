import marimo

__generated_with = "0.7.5"
app = marimo.App(width="medium", app_title="Facturation")


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


@app.cell
def __(cfne, cfns, meta, mo):
    mo.accordion({"Metadonnées": meta.dropna(axis=1, how='all'),
                  "Changements de fournisseur entrants": cfne.dropna(axis=1, how='all'),
                  "Changements de fournisseur sortants": cfns.dropna(axis=1, how='all')
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

    #_unused = ['zip_file', 'Id_Affaire']
    r151_start = get_r151_by_date(flux_path, start_date_picker.value)#.drop(columns=_unused)
    r151_end = get_r151_by_date(flux_path, end_date_picker.value)#.drop(columns=_unused)

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
    if not r151_start.empty:
        start_index = cfne.set_index('pdl').combine_first(r151_start.set_index('pdl'))
    else:
        start_index = cfne.set_index('pdl')
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
def parametrage_odoo(mo):
    # options={'Base dupliquée': 'https://edn-duplicate.odoo.com/', 
    #          'Base principale': 'https://energie-de-nantes.odoo.com/'},
    # options={'Base dupliquée': 'edn-duplicate', 
    #          'Base principale': 'energie-de-nantes'},
    dropdown = mo.ui.dropdown(
        options={'Base dupliquée': 'edn-duplicate', 
                 'Base principale': 'energie-de-nantes'},
        value='Base dupliquée',
        label='Choix de la base de donnée Odoo',
    )
    switch = mo.ui.switch(label="", value=True)
    mo.md(f"""
          # Données d'entrée : ODOO

          {dropdown}

          ### Sécurité : 
          Pour écrire dans la base Odoo, tu dois désactiver ce bouton de sécurité. Par défaut, les écritures dans la base Odoo seront simulées _(Il est recommandé de le faire une première fois en simulation avant de le faire pour de vrai.)_
          ### {switch}
          """)
    return dropdown, switch


@app.cell(hide_code=True)
def status_odoo(dropdown, env, mo, switch):
    from enedis_odoo_bridge.OdooAPI import OdooAPI
    _sim = switch.value
    odoo = OdooAPI(config=env, sim=_sim, url=f'https://{dropdown.value}.odoo.com/', db=dropdown.value,)

    _secu_msg = 'mais mode simulation est actif, **aucune donnée ne sera écrite dans la base Odoo**' if _sim else '**sois vigilant·e !**'
    danger_zone = dropdown.selected_key == 'Base principale'
    if danger_zone:
        _md = mo.md(f"""
                    Base de donnée : [{odoo.db}](https://{odoo.db}.odoo.com)

                    Tu interagis avec la base odoo **principale**, {_secu_msg} 
                    """)

    else :
        _md = mo.md(f"""
                    Base de donnée : [{odoo.db}](https://{odoo.db}.odoo.com)

                    Tu interagis avec la base odoo dupliquée, pas de bêtises possibles.
                    """)

    _callout = mo.callout(_md, kind='success' if _sim else 'danger')
    _callout
    return OdooAPI, danger_zone, odoo


@app.cell(hide_code=True)
def __(mo, odoo):
    mo.md(
        f"""
        ## Lancer le cycle de facturation
        ## Récupération des Abonnements à facturer

        On va chercher tous les abonnements en cours, dont le statut de facturation est _Facture brouillon créée_ ([voir vue kanban]({odoo.url}web#action=437&model=sale.order&view_type=kanban))
        """
    )
    return


@app.cell
def recuperation_abonnements_odoo(mo, odoo):
    _draft_orders_request = odoo.search_read('sale.order', filters=[[['state', '=', 'sale'], ['x_invoicing_state', '=', 'draft']]], fields=['id', 'x_pdl', 'invoice_ids', 'x_lisse', 'x_puissance_souscrite'])

    _stop_msg = mo.callout(mo.md(
        f"""
        ## ⚠ Aucun abonnement à facturer trouvé sur [{odoo.url}]({odoo.url}web#action=437&model=sale.order&view_type=kanban). ⚠ 
        Ici ne sont prises en comptes que les cartes dans la colonne **Facture brouillon créée**, et le programme n'en trouve pas.
        Le processus de facturation ne peut pas continuer en l'état. Plusieurs causes possibles : 
        1. Le processus de facturation n'a pas été lancé dans Odoo. Go le lancer. 
        2. Toutes les cartes abonnement ont déjà été déplacées dans une autre colonne. Si tu souhaite néanmoins re-mettre à jour un des abonnements, il suffit de redéplacer sa carte dans la colonne Facture brouillon créée. Attention, ça va écraser les valeurs de sa facture."""), kind='warn')

    mo.stop(_draft_orders_request.empty, _stop_msg)

    draft_orders = _draft_orders_request.set_index('x_pdl').sort_values(by='sale.order_id')
    draft_orders.rename(columns={'sale.order_id': 'order_id', 'invoice_ids': 'move_id'}, inplace=True)
    draft_orders['move_id'] = draft_orders['move_id'].apply(lambda x: max(x) if x else None)

    subs_to_display = [draft_orders]
    _no_invoices = draft_orders[draft_orders['move_id'].isna()]

    if not _no_invoices.empty:
        draft_orders.dropna(subset=['move_id'], inplace=True)
        subs_to_display.append(mo.callout("""Les abonnements suivants ont une facture et seront traités :""", kind='success'))
        subs_to_display.append(_no_invoices)
        subs_to_display.append(mo.callout("""Les abonnements suivants n'ont pas de facture et ne seront pas traités, il faudra le faire manuellement :""", kind='warn'))
    return draft_orders, subs_to_display


@app.cell
def recuperation_facture_odoo(draft_orders, mo, odoo, pd):
    _draft_invoices = odoo.read('account.move', ids=draft_orders['move_id'].to_list(), fields=['invoice_line_ids', 'state'])

    if not _draft_invoices.empty:
        draft_invoices = _draft_invoices[_draft_invoices['state'] == 'draft']
    else:
        draft_invoices = pd.DataFrame()

    _stop_msg = mo.callout(mo.md(
        f"""
        ## ⚠ Aucune facture brouillon trouvée sur [{odoo.url}]({odoo.url}web#action=437&model=account.move&view_type=list). ⚠ 
        Ici ne sont prises en comptes que les cartes dans la colonne **Facture brouillon créée**, et le programme n'en trouve pas.
        Le processus de facturation ne peut pas continuer en l'état. Plusieurs causes possibles : 
        1. Le processus de facturation n'a pas été lancé dans Odoo. Go le lancer. 
        2. Toutes les cartes abonnement ont déjà été déplacées dans une autre colonne. Si tu souhaite néanmoins re-mettre à jour un des abonnements, il suffit de redéplacer sa carte dans la colonne Facture brouillon créée. Attention, ça va écraser les valeurs de sa facture."""), kind='warn')

    mo.stop(draft_invoices.empty, _stop_msg)

    # Fusionner les DataFrames sur 'order_id' et assigner le résultat à draft_orders
    # Réinitialiser l'index avant la fusion
    draft_orders.reset_index(inplace=True)
    draft_invoices.reset_index(inplace=True)

    _merged = draft_orders.merge(draft_invoices[['account.move_id', 'invoice_line_ids']], left_on='move_id', right_on='account.move_id', how='left')
    #odoo_data = odoo.add_cat_fields(draft_orders, [])
    #draft_orders, draft_invoices, _merged
    _merged.set_index('x_pdl')
    odoo_data = odoo.add_cat_fields(_merged, []).set_index('x_pdl', drop=True)
    #odoo_data
    return draft_invoices, odoo_data


@app.cell(hide_code=True)
def __(draft_invoices, mo, odoo_data, subs_to_display):
    mo.accordion({f"Abonnements": mo.vstack(reversed(subs_to_display)),
                  f"Factures brouillon": draft_invoices,
                  f"Abonnements et factures": odoo_data
    })
    return


@app.cell
def __(mo):
    mo.md(r"# Fusion des données Enedis et Odoo")
    return


@app.cell
def fusion_enedis_odoo(DataFrame, consos, meta, odoo_data):
    # Fusionner draft_orders et meta en utilisant un left join
    merged_df = odoo_data.merge(meta, how='left', left_index=True, right_index=True)

    # Fusionner le résultat précédent avec consos en utilisant un left join
    merged_df = merged_df.merge(consos, how='left', left_index=True, right_index=True)

    import numpy as np
    def compute_missing_sums(df: DataFrame) -> DataFrame:

        df['HP'] = df[['HPH', 'HPB', 'HP']].sum(axis=1)
        df['HC'] = df[['HCH', 'HCB', 'HC']].sum(axis=1)
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
        return df
    merged_df = compute_missing_sums(merged_df)

    merged_df.dropna(axis=1, how='all')
    return compute_missing_sums, merged_df, np


@app.cell
def param_turpe(mo, pd):

    # Création du DataFrame avec les données du tableau
    _b = {
        "b": ["CU 4", "CU", "MU 4", "MU DT", "LU", "CU 4 – autoproduction collective", "MU 4 – autoproduction collective"],
        "€/kVA/an": [9.00, 9.96, 10.56, 12.24, 81.24, 9.00, 10.68]
    }
    b = pd.DataFrame(_b).set_index('b')
    _c = {
        "c": [
            "CU 4", "CU", "MU 4", "MU DT", "LU",
            "CU 4 - autoproduction collective, part autoproduite",
            "CU 4 - autoproduction collective, part alloproduite",
            "MU 4 - autoproduction collective, part autoproduite",
            "MU 4 - autoproduction collective, part alloproduite"
        ],
        "HPH c€/kWh": [
            6.67, 4.37, 6.12, 4.47, 1.10,
            1.64, 7.23, 1.64, 6.60
        ],
        "HCH c€/kWh": [
            4.56, 4.37, 4.24, 3.16, 1.10,
            1.29, 4.42, 1.29, 4.23
        ],
        "HPB c€/kWh": [
            1.43, 4.37, 1.39, 4.47, 1.10,
            0.77, 2.29, 0.77, 2.22
        ],
        "HCB c€/kWh": [
            0.88, 4.37, 0.87, 3.16, 1.10,
            0.37, 0.86, 0.37, 0.86
        ]
    }
    c = pd.DataFrame(_c).set_index('c')

    cg = 15.48
    cc = 19.9
    mo.md(
        f"""
        ## Calcul du Turpe

        Composante de Gestion annuelle $cg = {cg}$\n
        Composante de Comptage annuelle $cc = {cc}$
        
        """   
    )
    return b, c, cc, cg


@app.cell
def aff_param_turpe(b, c, mo):
    mo.vstack([
        mo.md(r"""
              ### Composante de soutirage
              
              \[
              CS = b \times P + \sum_{i=1}^{n} c_i \cdot E_i
              \]
              
              Dont part fixe $CSF = b \times P$
              Avec P = Puissance souscrite
              """),
        mo.hstack([b, c]), 
        mo.md(r"""
          ### Turpe Fixe journalier
          
          \[
          T_j = (cg + cc + b \times P)/365.25
          \]
          """),
        ]
    )
    return


@app.cell
def __(b, cc, cg, merged_df):

    # Calcul part fixe
    merged_df['turpe_fix_j'] = (cg + cc + b.at['CU 4', '€/kVA/an'] * merged_df['x_puissance_souscrite'])/365.25
    merged_df['turpe_fix'] = merged_df['turpe_fix_j'] * merged_df['j']
    merged_df[['order_id', 'HPH', 'HPB', 'HCH', 'HCB', 'HP', 'HC', 'BASE', 'turpe_fix']]
    return


@app.cell
def __(merged_df):
    merged_df['turpe_var'] = 0
    merged_df
    return


@app.cell
def __(danger_zone, mo, odoo):
    _db_kind = 'success' if not danger_zone else 'danger'
    _sim_kind = 'success' if odoo.sim else 'danger'
    _red_button_kind = 'success' if odoo.sim or not danger_zone else 'danger'
    _db = 'principale' if danger_zone else 'dupliquée/test'
    _sécu = 'Activée' if odoo.sim else 'Désactivée'
    _op = 'Simulation' if odoo.sim else 'Écriture'
    #_callout = mo.callout(mo.md(f"""La sécurité est **{_sécu}**"""), kind=_kind)
    red_button = mo.ui.run_button(kind=_red_button_kind, label=f'{_op} dans la base Odoo')
    mo.vstack([mo.md(f"""# Mise à jour dans Odoo"""),
               mo.hstack([
                   mo.callout(mo.md(f"""La sécurité est **{_sécu}**"""), kind=_sim_kind),
                   mo.callout(mo.md(f"""On utilise la base **{_db}**"""), kind=_db_kind),
                   red_button], justify='center', align='center')
               ])
    return red_button,


@app.cell
def __(mo, red_button):
    mo.stop(not red_button.value)
    #odoo.update_draft_invoices(merged_df, start_date_picker.value, end_date_picker.value)
    return


if __name__ == "__main__":
    app.run()
