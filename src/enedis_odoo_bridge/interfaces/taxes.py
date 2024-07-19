import marimo

__generated_with = "0.7.5"
app = marimo.App(width="medium", app_title="Facturation")


@app.cell
def __(mo):
    mo.md(
        r"""
        # Calcul de la CTA

        Données nécessaires par pdl : 
        1) Puissance souscrite
        2) FTA
        3) Jours facturés

        ### Puissance souscrite :
        source Odoo ou C15

        ### FTA :
        source Odoo ou C15

        ### Jours facturés :
        CFNE CFNS (donc R15) + dates début et fin période
        """
    )
    return


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
def param_flux(env, mo):
    from pathlib import Path
    flux_path = Path('~/data/flux_enedis/')
    mo.md(f"""
          # Données d'entrée : Flux Enedis
          **Serveur sFTP distant :** {env['FTP_ADDRESS']}\n
          **Dossier local :** {flux_path}
          """)
    return Path, flux_path


@app.cell(hide_code=True)
def __(end_date_picker, flux_path, mo, start_date_picker):
    from enedis_odoo_bridge.enedis_flux_engine import get_c15_by_date
    c15 = get_c15_by_date(flux_path, start_date_picker.value, end_date_picker.value)

    duplicates = c15[c15.duplicated(subset=['Id_PRM'], keep=False)]

    c15_latest = c15.sort_values(by='Date', ascending=False).drop_duplicates(subset=['Id_PRM'], keep='first').rename(columns={'Id_PRM':'pdl'}).set_index('pdl')

    mo.accordion({"C15": c15.dropna(axis=1, how='all'),
                  "Modifications": duplicates.dropna(axis=1, how='all'),
                  "Situation actuelle": c15_latest.dropna(axis=1, how='all')
                 })
    return c15, c15_latest, duplicates, get_c15_by_date


@app.cell
def __(mo):
    mo.md(r"### R15")
    return


@app.cell
def flux_r15(end_date_picker, flux_path, mo, start_date_picker):
    from enedis_odoo_bridge.enedis_flux_engine import get_r15_by_date, get_meta_from_r15, get_CF_from_r15
    r15 = get_r15_by_date(flux_path, start_date_picker.value, end_date_picker.value)
    meta = get_meta_from_r15(r15)
    cfne, cfns = get_CF_from_r15(r15)

    mo.accordion({"Metadonnées": meta.dropna(axis=1, how='all'),
                  "Changements de fournisseur entrants": cfne.dropna(axis=1, how='all'),
                  "Changements de fournisseur sortants": cfns.dropna(axis=1, how='all')
                 })
    return (
        cfne,
        cfns,
        get_CF_from_r15,
        get_meta_from_r15,
        get_r15_by_date,
        meta,
        r15,
    )


@app.cell
def __(cfne, end_date_picker):
    import pandas as pd
    from datetime import datetime
    cfne['end_date'] = pd.to_datetime(end_date_picker.value)
    cfne['j'] = (cfne['end_date'] - cfne['Date_Releve']).dt.days + 1
    cfne
    return datetime, pd


@app.cell
def __(cfne, merged_df, pd):
    cg = 15.48
    cc = 19.9
    tcta = 0.2193
    _b = {
        "b": ["CU 4", "CU", "MU 4", "MU DT", "LU", "CU 4 – autoproduction collective", "MU 4 – autoproduction collective"],
        "€/kVA/an": [9.00, 9.96, 10.56, 12.24, 81.24, 9.00, 10.68]
    }
    b = pd.DataFrame(_b).set_index('b')

    cfne['turpe_fix_j'] = (cg + cc + b.at['CU 4', '€/kVA/an'] * cfne['x_puissance_souscrite'])/365.25
    cfne['turpe_fix'] = cfne['turpe_fix_j'] * cfne['j']
    cfne['cta'] = tcta * merged_df['turpe_fix']
    return b, cc, cg, tcta


@app.cell
def __(mo):
    mo.md(
        r"""
        # TICFE
        https://www.impots.gouv.fr/taxes-interieures-de-consommation-tic

        En gros, on prend les MWh facturés, a la décimale qui correspond au kWh et on multiplie par 21.

        ## Arrondis fiscaux :
        Le montant total est arrondi à l'entier le plus proche

        ## LES ARRONDIS DÉCLARATIFS
        Les données portées dans les colonnes (A) « quantités » sont exprimées en mégawattheures et sont arrondies à l’unité sans décimale
        pour la TICGN (accise sur les gaz naturels) et la TICC (accise sur les charbons).
        Pour la TICFE (accise sur l’électricité), les quantités sont exprimées en fraction de MWh à 3 décimales soit l’équivalent du KWh (0,001 MWh).
        Les données portées dans les colonnes tarifaires (B) sont toutes exprimées en € par mégawattheure (€/MWh).
        Les données portées dans les colonnes « Montant A x B » sont arrondies à 2 décimales au centime d’€ à l’exception des lignes de
        totalisation qui sont arrondies à l’€.
        ## CADRE 1 : TICFE (Accise sur l’électricité)
        La taxe s’applique à l'électricité reprise au code NC 27161, quelle que soit la puissance souscrite.
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        r"""
        | Période                        | Tarif          | Description                                                                                       |
        |--------------------------------|----------------|---------------------------------------------------------------------------------------------------|
        | Du 1er février 2024 au 31 janvier 2025 | 20,50 €/MWh    | Tarif plein - Tarif pour les entreprises résultant de la sortie progressive du bouclier tarifaire |
        | Du 1er février 2024 au 31 janvier 2025 | 21 €/MWh       | Tarif plein - Tarif pour les ménages et assimilés résultant de la sortie progressive du bouclier tarifaire |
        """
    )
    return


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
