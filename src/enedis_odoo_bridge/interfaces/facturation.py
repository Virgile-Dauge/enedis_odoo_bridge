import marimo

__generated_with = "0.7.17"
app = marimo.App(width="medium", app_title="Facturation")


@app.cell
def delimitation_periode():
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
def param_flux(env, mo):
    from pathlib import Path
    flux_path = Path('~/data/flux_enedis/')

    switch_edn_only = mo.ui.switch(label="Filtrage pdl EDN", value=True)
    mo.md(f"""
          # Données d'entrée : Flux Enedis

          ## Paramètres
          Source ftp : {env['FTP_ADDRESS']}
          
          Dossier source : {flux_path}
          ## Filtrage
          Les flux Enedis contiennement toutes les données du périmètre, donc à la fois des pdl que nous gérons nous et des pdl       gérès parcelleux qui utilisent notre agrément. Il est possible de filtrer pour n'avoir que les notres en allant             chercher sur odoo la liste des abonnements actifs.  
          {switch_edn_only}
          """)
    return Path, flux_path, switch_edn_only


@app.cell(hide_code=True)
def get_pdl(env, mo):
    from enedis_odoo_bridge.odoo import get_valid_subscriptions_pdl
    pdl_actifs = get_valid_subscriptions_pdl(env)

    mo.md(f'''## Abonnements en cours
              {len(pdl_actifs)} abonnements en cours d'après Odoo
           ''')
    return get_valid_subscriptions_pdl, pdl_actifs


@app.cell(hide_code=True)
def flux_c15(
    end_date_picker,
    flux_path,
    pd,
    pdl_actifs,
    start_date_picker,
    switch_edn_only,
):
    from enedis_odoo_bridge.enedis_flux_engine import get_c15_by_date
    c15 = get_c15_by_date(flux_path, start_date_picker.value, end_date_picker.value).rename(columns={'Id_PRM':'pdl'})
    if switch_edn_only.value:
        c15 = c15[c15['pdl'].isin(pdl_actifs)]
    c15['Date_Evenement'] = pd.to_datetime(c15['Date_Evenement']).dt.date

    c15['start_date'] = start_date_picker.value
    c15['start_date'] = pd.to_datetime(c15['start_date']).dt.date

    c15['end_date'] = end_date_picker.value
    c15['end_date'] = pd.to_datetime(c15['end_date']).dt.date

    c15_latest = c15.sort_values(by='Date_Evenement', ascending=False).drop_duplicates(subset=['pdl'], keep='first').set_index('pdl')

    c15 = c15[c15['Date_Evenement'] >= c15['start_date']]
    c15 = c15[c15['Date_Evenement'] <= c15['end_date']]
    c15 = c15.drop(columns=['start_date', 'end_date'])

    influx = c15[c15['Nature_Evenement'].isin(['CFNE', 'MES'])].set_index('pdl')
    outflux = c15[c15['Nature_Evenement'].isin(['CFNS', 'RES'])].set_index('pdl')
    return c15, c15_latest, get_c15_by_date, influx, outflux


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        r"""
        ### Données contractuelles issues du C15

        A Vérifier : PK le filtrage ne donne que 73 sitations actuelles alors qu'Odoo renvoie 76 abonnements ?
        """
    )
    return


@app.cell(hide_code=True)
def aff_c15(c15, c15_latest, influx, mo, outflux):
    _duplicates = c15[c15.duplicated(subset=['pdl'], keep=False)]

    mo.accordion({"Variations C15 dans la période": c15.dropna(axis=1, how='all'),
                  "Doublons": _duplicates.sort_values(by=['pdl', 'Date_Evenement']).dropna(axis=1, how='all').reset_index(),
                  "MES et CFNE": influx.dropna(axis=1, how='all').reset_index(),
                  "RES et CFNS": outflux.dropna(axis=1, how='all').reset_index(),
                  "Situation actuelle": c15_latest.dropna(axis=1, how='all').reset_index()
                 })
    return


@app.cell
def __(mo):
    mo.md("""### R15""")
    return


@app.cell(hide_code=True)
def flux_r15(
    end_date_picker,
    flux_path,
    mo,
    pdl_actifs,
    start_date_picker,
    switch_edn_only,
):
    from enedis_odoo_bridge.enedis_flux_engine import get_r15_by_date, get_meta_from_r15, get_CF_from_r15
    r15 = get_r15_by_date(flux_path, start_date_picker.value, end_date_picker.value)

    if switch_edn_only.value:
        r15 = r15[r15.index.isin(pdl_actifs)]
    meta = get_meta_from_r15(r15)
    #cfne, cfns = get_CF_from_r15(r15)

    mo.accordion({"Metadonnées": meta.dropna(axis=1, how='all'),
                  #"Changements de fournisseur entrants": cfne.dropna(axis=1, how='all'),
                  #"Changements de fournisseur sortants": cfns.dropna(axis=1, how='all')
                 })
    return get_CF_from_r15, get_meta_from_r15, get_r15_by_date, meta, r15


@app.cell
def __(mo):
    mo.md("""### R151""")
    return


@app.cell(hide_code=True)
def flux_r151(
    end_date_picker,
    flux_path,
    mo,
    pdl_actifs,
    start_date_picker,
    switch_edn_only,
):
    from enedis_odoo_bridge.enedis_flux_engine import get_r151_by_date
    from enedis_odoo_bridge.utils import get_consumption_names

    _unused = ['zip_file', 'Id_Affaire']
    start_index = get_r151_by_date(flux_path, start_date_picker.value).set_index('pdl').drop(columns=_unused)
    end_index = get_r151_by_date(flux_path, end_date_picker.value)

    mo.stop(end_index.empty, mo.callout(mo.md(f'Pas de données du {end_date_picker.value} dans le R151 !'),kind='warn'))
    end_index = end_index.set_index('pdl').drop(columns=_unused)

    # On filtre avec juste nos PDL si nécessaire
    if switch_edn_only.value:
        start_index = start_index[start_index.index.isin(pdl_actifs)]
        end_index = end_index[end_index.index.isin(pdl_actifs)]

    # On converti en kWh
    conso_cols = [c for c in get_consumption_names() if c in start_index]
    start_index[conso_cols] = (start_index[conso_cols] / 1000).round()
    #_conso_cols = [c for c in get_consumption_names() if c in end_index]
    end_index[conso_cols] = (end_index[conso_cols] / 1000).round()

    # Trouver les PDLs communs
    #_pdls_communs = start_index.index.intersection(end_index.index)

    # Calculer la différence pour les colonnes spécifiées
    #consos = end_index.loc[_pdls_communs, _conso_cols] - start_index.loc[_pdls_communs, _conso_cols]

    mo.accordion({f"Index du {start_date_picker.value}": start_index.dropna(axis=1, how='all'),
                  f"Index du {end_date_picker.value}": end_index.dropna(axis=1, how='all'),
                  #"Consommations": consos.dropna(axis=1, how='all'),
    })
    return (
        conso_cols,
        end_index,
        get_consumption_names,
        get_r151_by_date,
        start_index,
    )


@app.cell
def __(mo):
    mo.md(r"""# Fusion""")
    return


@app.cell(hide_code=True)
def __():
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Polygon
    import matplotlib.font_manager as font_manager
    import matplotlib.cm as cm

    def plot_data_merge(sources_list, reference_name):
        """
        Cette fonction crée un graphique illustrant la construction d'une matrice à partir de plusieurs sources,
        avec une colonne de référence commune, en utilisant la colormap 'Set3' et affichant les noms de colonnes en vertical.
        
        :param sources_list: Une liste de tuples où le premier élément est le nom de la source et le second est la liste des noms de colonnes.
        :param reference_name: Le nom de la référence commune utilisée pour la fusion des sources.
        """
        fig, ax = plt.subplots(figsize=(12, 6), dpi=300)

        # Paramètres pour l'affichage
        rect_width = 0.03
        rect_height = 0.3  # Augmentation de la hauteur des rectangles pour ressembler plus à des colonnes
        y_start = 0.85
        spacing = rect_width * 2  # Espace entre les matrices équivalent à deux colonnes
        reference_width = 0.015  # Largeur de la colonne de référence
        edge_color = '#4d4d4d'  # Gris foncé pour les traits
        edge_linewidth = 1.5  # Épaisseur des traits réduite

        title_fontsize = 14  # Taille de la police des titres
        text_fontsize = 12  # Taille de la police des textes

        # Choisir une police moderne
        font_properties = font_manager.FontProperties(family='DejaVu Sans', weight='bold')

        # Utiliser la colormap 'Set3' pour générer des couleurs pour chaque source
        cmap = cm.get_cmap('Set3', len(sources_list))
        colors = [cmap(i) for i in range(len(sources_list))]

        x_start = 0.1
        source_positions = []

        # Afficher les rectangles représentant les colonnes des matrices sources côte à côte avec les noms des sources
        for i, (source_name, columns) in enumerate(sources_list):
            source_positions.append((x_start, len(columns)))

            # Ajouter la colonne de référence
            ref_rect = plt.Rectangle((x_start - reference_width, y_start), reference_width, rect_height, color='#d3d3d3', ec=edge_color, linestyle='--', linewidth=edge_linewidth)
            ax.add_patch(ref_rect)
            ax.text(x_start - reference_width / 2, y_start + rect_height / 2, reference_name, ha='center', va='center', fontsize=text_fontsize, rotation=90, fontproperties=font_properties)

            ax.text(x_start + rect_width * (len(columns) - 1) / 2, y_start + rect_height + 0.02, source_name, ha='center', va='center', fontsize=title_fontsize, fontweight='bold', color=edge_color, fontproperties=font_properties)
            for j, col in enumerate(columns):
                rect = plt.Rectangle((x_start + j * rect_width, y_start), rect_width, rect_height, color=colors[i], ec=edge_color, linewidth=edge_linewidth)
                ax.add_patch(rect)
                ax.text(x_start + j * rect_width + rect_width / 2, y_start + rect_height / 2, col, ha='center', va='center', fontsize=text_fontsize, rotation=90, fontproperties=font_properties)

            x_start += len(columns) * rect_width + spacing

        # Afficher les rectangles représentant les colonnes de la matrice finale
        y_final = 0.4
        total_source_width = x_start - spacing  # Largeur totale de toutes les sources combinées
        final_matrix_width = len([col for _, columns in sources_list for col in columns]) * rect_width
        x_start_final = 0.1 + (total_source_width - final_matrix_width) / 2  # Centrer la matrice finale

        # Ajouter la colonne de référence pour la matrice finale
        ref_rect = plt.Rectangle((x_start_final - reference_width, y_final), reference_width, rect_height, color='#d3d3d3', ec=edge_color, linestyle='--', linewidth=edge_linewidth)
        ax.add_patch(ref_rect)
        ax.text(x_start_final - reference_width / 2, y_final + rect_height / 2, reference_name, ha='center', va='center', fontsize=text_fontsize, rotation=90, fontproperties=font_properties)

        all_columns = [col for _, columns in sources_list for col in columns]
        for i, col in enumerate(all_columns):
            rect = plt.Rectangle((x_start_final + i * rect_width, y_final), rect_width, rect_height, color='#e78ac3', ec=edge_color, linewidth=edge_linewidth)
            ax.add_patch(rect)
            ax.text(x_start_final + i * rect_width + rect_width / 2, y_final + rect_height / 2, col, ha='center', va='center', fontsize=text_fontsize, rotation=90, fontproperties=font_properties)

        # Ajouter le titre "Matrice Finale"
        ax.text(x_start_final + (len(all_columns) * rect_width) / 2, 0.35, 'Matrice Finale', ha='center', va='center', fontsize=title_fontsize, fontweight='bold', color=edge_color, fontproperties=font_properties)

        # Dessiner les polygones pour représenter l'ombre suivant les tracés des lignes et des côtés des rectangles
        current_index = 0
        for (x_start_line_left, num_columns), (_, columns) in zip(source_positions, sources_list):
            x_start_line_right = x_start_line_left + rect_width * (num_columns - 1)

            polygon = Polygon([
                (x_start_line_left, y_start),  # Point gauche du premier rectangle
                (x_start_line_right + rect_width, y_start),  # Point droit du dernier rectangle
                (x_start_final + (current_index + len(columns) - 1) * rect_width + rect_width, y_final + rect_height),  # Point droit du rectangle final
                (x_start_final + current_index * rect_width, y_final + rect_height)  # Point gauche du rectangle final
            ], closed=True, color='grey', alpha=0.3)

            ax.add_patch(polygon)

            # Lignes reliant les rectangles des sources à la matrice finale
            ax.plot([x_start_line_left, x_start_final + current_index * rect_width], [y_start, y_final + rect_height], color=edge_color, linewidth=edge_linewidth)
            ax.plot([x_start_line_right + rect_width, x_start_final + (current_index + len(columns) - 1) * rect_width + rect_width], [y_start, y_final + rect_height], color=edge_color, linewidth=edge_linewidth)

            current_index += len(columns)

        # Enlever les axes
        ax.axis('off')

        # Afficher la figure
        plt.show()
    return Polygon, Rectangle, cm, font_manager, plot_data_merge, plt


@app.cell
def __(end_date_picker, plot_data_merge, start_date_picker):
    _graphique_data = [
        ('C15 (actuel)', ['FTA', 'Puissance', 'Num_Depannage']),
        ('C15 (IN)', ['date IN', 'index IN']),
        ('C15 (OUT)', ['date OUT', 'index OUT']),
        ('R15', ['Type_Compteur', 'Num_Serie']),
        ('R151', [f'index {start_date_picker.value}', f'index {end_date_picker.value}']),
        #('F15', ['data1_C', 'data2_C', 'data3_C', 'data4_C']),
    ]

    plot_data_merge(_graphique_data, 'pdl')
    return


@app.cell
def __(c15_latest, conso_cols, influx):
    merged_enedis_data = c15_latest[['Formule_Tarifaire_Acheminement', 'Puissance_Souscrite', 'Num_Depannage']].merge(
        influx[['Date_Evenement']+conso_cols], how='left', left_index=True, right_index=True,)
    merged_enedis_data
    return merged_enedis_data,


@app.cell
def param_odoo(mo):
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


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
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

    _merged.set_index('x_pdl')
    odoo_data = odoo.add_cat_fields(_merged, []).set_index('x_pdl', drop=True)
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
    mo.md(
        """
        # Fusion des données Enedis et Odoo

        On part des contracts et factures Odoo (`odoo_data`), puis :

        - On y ajoute lorsque connus les index de début et de fin issus du R151 (`start_index` et `end_index`)
        - Si lieu, on remplace les index et les dates de début/fin par les données de changements contractuelles issues du C15 (`influx` et `outflux`)
        - On ajoute les métadonnées Type compteur et Num Compteur depuis le R15
        - On récupère les données de puissance et FTA depuis le C15 `c15_latest`
        - On peut ensuite calculer la différence entre les index de début et de fin, ainsi que le nb de jours
        """
    )
    return


@app.cell
def calculs_consos(
    DataFrame,
    c15_latest,
    conso_cols,
    end_date_picker,
    end_index,
    influx,
    meta,
    odoo_data,
    outflux,
    pd,
    start_date_picker,
    start_index,
):
    import numpy as np

    # Fusionner les données Odoo avec les index de début et de fin issus du R151
    _start_conso_cols = {c: 'start_'+ c for c in conso_cols}
    _end_conso_cols = {c: 'end_'+ c for c in conso_cols}

    merged_data = odoo_data.merge(start_index[conso_cols].rename(columns=_start_conso_cols), 
                                  how='left', 
                                  left_index=True, right_index=True,)# suffixes=('', '_start'))
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
    return conso_col, end_col, merged_data, np, start_col


@app.cell(hide_code=True)
def param_taxes(mo, pd):
    # Création du DataFrame avec les données du tableau
    _b = {
        "b": ["CU4", "CUST", "MU4", "MUDT", "LU", "CU4 – autoproduction collective", "MU4 – autoproduction collective"],
        "€/kVA/an": [9.00, 9.96, 10.56, 12.24, 81.24, 9.00, 10.68]
    }
    b = pd.DataFrame(_b).set_index('b')
    _c = {
        "c": [
            "CU4", "CUST", "MU4", "MUDT", "LU",
            "CU 4 - autoproduction collective, part autoproduite",
            "CU 4 - autoproduction collective, part alloproduite",
            "MU 4 - autoproduction collective, part autoproduite",
            "MU 4 - autoproduction collective, part alloproduite"
        ],
        "HPH": [
            6.67, 0, 6.12, 0, 0,
            1.64, 7.23, 1.64, 6.60
        ],
        "HCH": [
            4.56, 0, 4.24, 0, 0,
            1.29, 4.42, 1.29, 4.23
        ],
        "HPB": [
            1.43, 0, 1.39, 0, 0,
            0.77, 2.29, 0.77, 2.22
        ],
        "HCB": [
            0.88, 0, 0.87, 0, 0,
            0.37, 0.86, 0.37, 0.86
        ],
        "HP": [
            0, 0, 0, 4.47, 0,
            0, 0, 0, 0
        ],
        "HC": [
            0, 0, 0, 3.16, 0,
            0, 0, 0, 0
        ],
        "BASE": [
            0, 4.37, 0, 0, 1.10,
            0, 0, 0, 0
        ]
    }
    c = pd.DataFrame(_c).set_index('c')

    cg = 15.48
    cc = 19.9
    tcta = 0.2193
    mo.md(
        f"""
        ## Calcul du Turpe

        Composante de Gestion annuelle $cg = {cg}$\n
        Composante de Comptage annuelle $cc = {cc}$\n
        Cta $cta = {tcta} * turpe fixe$
        """   
    )
    return b, c, cc, cg, tcta


@app.cell(hide_code=True)
def aff_param_taxes(b, c, mo):
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
          T_j = (cg + cc + b \times P)/366
          \]
          """),
        ]
    )
    return


@app.cell
def taxes_fixes(b, cc, cg, merged_data, np, tcta):
    # Calcul part fixe
    def _get_tarif(row):
        key = row['Formule_Tarifaire_Acheminement'].replace('BTINF', '')
        if key in b.index:
            return b.at[key, '€/kVA/an']
        else:
            return np.nan

    # On récupére les valeurs de b en fonction de la FTA
    merged_data['b'] = merged_data.apply(_get_tarif, axis=1)
    merged_data['Puissance_Souscrite'] = merged_data['Puissance_Souscrite'].astype(float)

    merged_data['turpe_fix_j'] = (cg + cc + merged_data['b'] * merged_data['Puissance_Souscrite'])/366
    merged_data['turpe_fix'] = merged_data['turpe_fix_j'] * merged_data['j']
    merged_data['cta'] = tcta * merged_data['turpe_fix']
    merged_data
    return


@app.cell
def taxes_variables(c, merged_data):
    def _calc_sum_ponderated(row):
        key = row['Formule_Tarifaire_Acheminement'].replace('BTINF', '')
        if key in c.index:
            coef = c.loc[key]
            conso_cols = ['HPH', 'HCH', 'HPB', 'HCB', 'HP', 'HC', 'BASE']
            return sum(row[col] * coef[col] for col in conso_cols)/100
        else:
            print(key)
            return 0
    merged_data['turpe_var'] = merged_data.apply(_calc_sum_ponderated, axis=1)
    merged_data['turpe'] = merged_data['turpe_fix'] + merged_data['turpe_var']
    merged_data
    return


@app.cell(hide_code=True)
def confirm_maj_odoo(danger_zone, mo, odoo):
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
def maj_odoo(
    end_date_picker,
    merged_data,
    mo,
    odoo,
    red_button,
    start_date_picker,
):
    mo.stop(not red_button.value)

    # Préparation des données 
    merged_data['update_dates'] = merged_data['j'] != (end_date_picker.value - start_date_picker.value).days + 1

    odoo.update_draft_invoices(merged_data.rename(columns={'BASE': 'Base', 'j': 'subscription_days'}))
    return


if __name__ == "__main__":
    app.run()
