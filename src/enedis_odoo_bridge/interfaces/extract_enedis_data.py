import marimo

__generated_with = "0.8.0"
app = marimo.App(width="medium", app_title="extract_enedis_data")


@app.cell
async def __():
    from download import app
    # execute the notebook
    result = await app.embed()
    return app, result


@app.cell
def __(result):
    result.output
    return


@app.cell
def delimitation_periode():
    import marimo as mo
    import pandas as pd
    import numpy as np
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
        np,
        pd,
        start_date_picker,
    )


@app.cell(hide_code=True)
def param_flux(mo):
    from pathlib import Path
    flux_path = Path('~/data/flux_enedis/')

    switch_edn_only = mo.ui.switch(label="Filtrage pdl EDN", value=True)
    mo.md(f"""
          # Données d'entrée : Flux Enedis

          ## Paramètres
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


@app.cell
def flux_c15(
    end_date_picker,
    flux_path,
    pd,
    pdl_actifs,
    start_date_picker,
    switch_edn_only,
):
    from enedis_odoo_bridge.enedis_flux_engine import get_c15_by_date
    _c15 = get_c15_by_date(flux_path, start_date_picker.value, end_date_picker.value)
    if switch_edn_only.value:
        _c15 = _c15[_c15['pdl'].isin(pdl_actifs)]
    _c15['date'] = pd.to_datetime(_c15['date']).dt.date

    _c15['start_date'] = start_date_picker.value
    _c15['start_date'] = pd.to_datetime(_c15['start_date']).dt.date

    _c15['end_date'] = end_date_picker.value
    _c15['end_date'] = pd.to_datetime(_c15['end_date']).dt.date

    c15_latest = _c15.sort_values(by='date', ascending=False).drop_duplicates(subset=['pdl'], keep='first')

    _c15 = _c15[_c15['date'] >= _c15['start_date']]
    _c15 = _c15[_c15['date'] <= _c15['end_date']]
    #c15 = c15.drop(columns=['start_date', 'end_date'])

    influx = _c15[_c15['Nature_Evenement'].isin(['CFNE', 'MES'])]
    outflux = _c15[_c15['Nature_Evenement'].isin(['CFNS', 'RES'])]
    return c15_latest, get_c15_by_date, influx, outflux


@app.cell
def __(mo):
    mo.md(r"""### Données contractuelles issues du C15""")
    return


@app.cell(hide_code=True)
def aff_c15(c15_latest, influx, mo, outflux):
    #_duplicates = _c15[c15.duplicated(subset=['pdl'], keep=False)]

    mo.accordion({#"Variations C15 dans la période": c15.dropna(axis=1, how='all'),
                  #"Doublons": _duplicates.sort_values(by=['pdl', 'Date_Evenement']).dropna(axis=1, how='all').reset_index(),
                  "IN (MES et CFNE)": influx.dropna(axis=1, how='all'),
                  "OUT (RES et CFNS)": outflux.dropna(axis=1, how='all'),
                  "Situation actuelle": c15_latest.dropna(axis=1, how='all')
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
    _r15 = get_r15_by_date(flux_path, start_date_picker.value, end_date_picker.value)

    if switch_edn_only.value:
        _r15 = _r15[_r15['pdl'].isin(pdl_actifs)]
    meta = get_meta_from_r15(_r15)

    mo.accordion({"R15": _r15.dropna(axis=1, how='all'),
                  "Metadonnées": meta.dropna(axis=1, how='all'),
                 })
    return get_CF_from_r15, get_meta_from_r15, get_r15_by_date, meta


@app.cell
def __(mo):
    mo.md("""### R151""")
    return


@app.cell
def flux_r151(
    end_date_picker,
    flux_path,
    mo,
    np,
    pdl_actifs,
    start_date_picker,
    switch_edn_only,
):
    from enedis_odoo_bridge.enedis_flux_engine import get_r151_by_date
    from enedis_odoo_bridge.utils import get_consumption_names

    _unused = ['Id_Affaire']
    start_index = get_r151_by_date(flux_path, start_date_picker.value).drop(columns=_unused)
    end_index = get_r151_by_date(flux_path, end_date_picker.value)

    mo.stop(end_index.empty, mo.callout(mo.md(f'Pas de données du {end_date_picker.value} dans le R151 !'),kind='warn'))
    end_index = end_index.drop(columns=_unused)

    # On filtre avec juste nos PDL si nécessaire
    if switch_edn_only.value:
        start_index = start_index[start_index['pdl'].isin(pdl_actifs)]
        end_index = end_index[end_index['pdl'].isin(pdl_actifs)]

    # On ajoute 
    start_index['BASE'] = np.nan
    end_index['BASE'] = np.nan
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


@app.cell
def __():
    #selection = mo.ui.table(data=c15_latest, label='Sélectione les pdl à prendre en compte')
    #selection
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


@app.cell(hide_code=True)
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
def fusion_enedis(
    c15_latest,
    conso_cols,
    end_index,
    influx,
    meta,
    mo,
    outflux,
    start_index,
):
    # Base : C15 Actuel
    _merged_enedis_data = c15_latest[['pdl', 'FTA', 'P', 'depannage']]
    #_merged_enedis_data = selection.value[['pdl', 'FTA', 'P', 'depannage']]
    def _merge_with_prefix(A, B, prefix):
        return A.merge(B.add_prefix(prefix),
                       how='left', left_on='pdl', right_on=f'{prefix}pdl').drop(columns=[f'{prefix}pdl'])
    # Fusion C15 IN
    _merged_enedis_data = _merge_with_prefix(_merged_enedis_data,
                                            influx[['pdl', 'date']+conso_cols],
                                            'in_')

    # Fusion + C15 OUT
    _merged_enedis_data = _merge_with_prefix(_merged_enedis_data,
                                            outflux[['pdl', 'date']+conso_cols],
                                            'out_')

    # Fusion + R15 (meta)
    _merged_enedis_data = _merged_enedis_data.merge(
        meta[['pdl', 'Type_Compteur', 'Num_Serie']], 
        how='left', on='pdl',)

    # Fusion + R151 (start)
    _merged_enedis_data = _merge_with_prefix(_merged_enedis_data,
                                            start_index[['pdl']+conso_cols],
                                            'start_')
    # Fusion + R151 (end)
    _merged_enedis_data = _merge_with_prefix(_merged_enedis_data,
                                            end_index[['pdl']+conso_cols],
                                            'end_')
    # Specify the column to check for duplicates
    _duplicate_column_name = 'pdl'

    # Identify duplicates
    _duplicates_df = _merged_enedis_data[_merged_enedis_data.duplicated(subset=[_duplicate_column_name], keep=False)]

    # Drop duplicates from the original DataFrame
    enedis_data = _merged_enedis_data.drop_duplicates(subset=[_duplicate_column_name]).copy()

    if not _duplicates_df.empty:
        _to_ouput = mo.vstack([mo.callout(mo.md(f"""
                                                **Attention: Il y a {len(_duplicates_df)} entrées dupliquées dans les données !**
                                                Pour la suite, le pdl problématique sera écarté, les duplicatas sont affichés ci-dessous."""), kind='warn'),
                               _duplicates_df.dropna(axis=1, how='all')])
    else:
        _to_ouput = mo.callout(mo.md(f'Fusion réussie'), kind='success')
        
    _to_ouput
    return enedis_data,


@app.cell
def __(enedis_data, mo):
    mo.vstack([mo.md("# Résultat de l'extraction des données Enedis :"), enedis_data.dropna(axis=1, how='all')])
    return


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        r"""
        # Calculs des consos
        ## Choix des index

        Principe : A partir des données d'Enedis, on choisit les index à utiliser : 

        Pour l'index de début de période, on choisit une entrée (CFNE ou MES) si elle existe, sinon on utilise l'index donné par le flux d'index quotidiens (R151) du premier jour de la période.

        Pour l'index de fin de période, on choisit une sortie (CFNs ou RES) si elle existe, sinon on utilise l'index donné par le flux d'index quotidiens (R151) du dernier jour de la période.
        """
    )
    return


@app.cell(hide_code=True)
def choix_index(
    end_date_picker,
    enedis_data,
    get_consumption_names,
    np,
    pd,
    start_date_picker,
):
    _cols = get_consumption_names()
    for _col in _cols:
        enedis_data[f'd_{_col}'] = np.where(enedis_data['in_date'].notna(),
                                                  enedis_data[f'in_{_col}'],
                                                  enedis_data[f'start_{_col}'])

    for _col in _cols:
        enedis_data[f'f_{_col}'] = np.where(enedis_data['out_date'].notna(),
                                                  enedis_data[f'out_{_col}'],
                                                  enedis_data[f'end_{_col}'])

    enedis_data['start_date'] = start_date_picker.value
    enedis_data['start_date'] = pd.to_datetime(enedis_data['start_date']).dt.date

    enedis_data['end_date'] = end_date_picker.value
    enedis_data['end_date'] = pd.to_datetime(enedis_data['end_date']).dt.date

    enedis_data[f'd_date'] = np.where(enedis_data['in_date'].notna(),
                                         enedis_data[f'in_date'],
                                         enedis_data[f'start_date'])
    enedis_data[f'f_date'] = np.where(enedis_data['out_date'].notna(),
                                         enedis_data[f'out_date'],
                                         enedis_data[f'end_date'])
    return


@app.cell
def __(mo):
    mo.md(
        r"""
        ## Soustraction des index

        On prend l'index de fin sélectionné précédemment, et on y soustrait l'index de début
        """
    )
    return


@app.cell(hide_code=True)
def consommations(DataFrame, enedis_data, get_consumption_names, np, pd):
    _cols = get_consumption_names()
    for _col in _cols:
        enedis_data[f'{_col}'] = enedis_data[f'f_{_col}'] - enedis_data[f'd_{_col}']
    enedis_data.dropna(axis=1, how='all')

    def _compute_missing_sums(df: DataFrame) -> DataFrame:
        if 'BASE' not in df.columns:
            df['BASE'] = np.nan  

        df['missing_data'] = df[['HPH', 'HPB', 'HCH', 
                'HCB', 'BASE', 'HP',
                'HC']].isna().all(axis=1)
        df['BASE'] = np.where(
                df['missing_data'],
                np.nan,
                df[['HPH', 'HPB', 'HCH', 
                'HCB', 'BASE', 'HP', 
                'HC']].sum(axis=1)
            )
        df['HP'] = df[['HPH', 'HPB', 'HP']].sum(axis=1)
        df['HC'] = df[['HCH', 'HCB', 'HC']].sum(axis=1)
        return df.copy()
    consos = _compute_missing_sums(enedis_data)[['pdl', 'FTA', 'P', 'depannage', 'Type_Compteur', 'Num_Serie', 'missing_data', 'd_date', 'f_date']+_cols]

    consos['j'] = (pd.to_datetime(consos['f_date']) - pd.to_datetime(consos['d_date'])).dt.days + 1
    consos
    return consos,


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
        # Calcul des taxes

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
def __(mo):
    mo.md(r"""## Données Enedis agregées et conso""")
    return


@app.cell
def taxes(b, c, cc, cg, consos, np, tcta):
    # Calcul part fixe
    def _get_tarif(row):
        key = row['FTA'].replace('BTINF', '')
        if key in b.index:
            return b.at[key, '€/kVA/an']
        else:
            return np.nan

    # On récupére les valeurs de b en fonction de la FTA
    consos['b'] = consos.apply(_get_tarif, axis=1)
    consos['P'] = consos['P'].astype(float)

    consos['turpe_fix_j'] = (cg + cc + consos['b'] * consos['P'])/366
    consos['turpe_fix'] = consos['turpe_fix_j'] * consos['j']
    consos['cta'] = tcta * consos['turpe_fix']

    def _calc_sum_ponderated(row):
        key = row['FTA'].replace('BTINF', '')
        if key in c.index:
            coef = c.loc[key]
            conso_cols = ['HPH', 'HCH', 'HPB', 'HCB', 'HP', 'HC', 'BASE']
            return sum(row[col] * coef[col] for col in conso_cols)/100
        else:
            print(key)
            return 0
    consos['turpe_var'] = consos.apply(_calc_sum_ponderated, axis=1)
    consos['turpe'] = consos['turpe_fix'] + consos['turpe_var']
    consos
    return


if __name__ == "__main__":
    app.run()
