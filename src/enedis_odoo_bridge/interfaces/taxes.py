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


@app.cell
def flux_c15(end_date_picker, flux_path, start_date_picker):
    import pandas as pd
    from datetime import datetime
    from enedis_odoo_bridge.enedis_flux_engine import get_c15_by_date
    c15 = get_c15_by_date(flux_path, start_date_picker.value, end_date_picker.value)
    c15['Date_Evenement'] = pd.to_datetime(c15['Date_Evenement']).dt.date

    c15['end_date'] = end_date_picker.value
    c15['end_date'] = pd.to_datetime(c15['end_date']).dt.date
    c15 = c15[c15['Date_Evenement'] <= c15['end_date']]
    return c15, datetime, get_c15_by_date, pd


@app.cell
def tri_flux_c15(c15, mo):

    duplicates = c15[c15.duplicated(subset=['Id_PRM'], keep=False)]

    influx = c15[c15['Nature_Evenement'].isin(['CFNE', 'MES'])]
    outflux = c15[c15['Nature_Evenement'].isin(['CFNS', 'RES'])]
    c15_latest = c15.sort_values(by='Date_Evenement', ascending=False).drop_duplicates(subset=['Id_PRM'], keep='first').rename(columns={'Id_PRM':'pdl'}).set_index('pdl')

    mo.accordion({"C15": c15.dropna(axis=1, how='all'),
                  "Doublons": duplicates.sort_values(by=['Id_PRM', 'Date_Evenement']),
                  "MES et CFNE": influx,
                  "RES et CFNS": outflux,
                  "Situation actuelle": c15_latest.dropna(axis=1, how='all')
                 })
    return c15_latest, duplicates, influx, outflux


@app.cell
def __(mo):
    mo.md(
        r"""
        ## Nb jours à facturer. 

        Cette fois-ci comme c'est la première fois on ne va faire qu'à partir des CFNE ou MES, sinon il faudra aussi prendre en compte le reste comme une période complète.  
        """
    )
    return


@app.cell
def param_taxes(pd):
    cg = 15.48
    cc = 19.92
    tcta = 0.2193
    _b = {
        "b": ["CU4", "CUST", "MU4", "MUDT", "LU", "CU4 – autoproduction collective", "MU4 – autoproduction collective"],
        "€/kVA/an": [9.00, 9.96, 10.56, 12.24, 81.24, 9.00, 10.68]
    }
    b = pd.DataFrame(_b).set_index('b')
    return b, cc, cg, tcta


@app.cell
def __(b, cc, cg, mo):

    mo.vstack([
        mo.md(r"""
              ## Nombre de jours 
              \[
              j =   end date - Date Evenement + 1
              \]

              Avec `Date_Evenement` = `Date cfne` puisqu'on a pris que les CFNE
              """),
        
        mo.md(r"""
              ## Turpe Fixe journalier
              
              \[
              turpe fixe_j = \frac{cg + cc + b \times P}{366}
              \]
              """),
        mo.hstack([mo.md(f"""
                          Avec :\n
                          Composante annuelle de Gestion cg = {cg}\n
                          Composante annuelle de Comptage cc = {cc}\n
                          Partie fixe de la composante annuelle de soutirage b =
                          """),
                   b]),
        mo.md(r"""
              ## Turpe Fixe
              
              \[
              turpe fixe = turpe fixe_j \times j
              \]
              """),
        mo.md(r"""
              ## CTA
              
              \[
              CTA = taux_{cta} \times turpe fixe
              \]
              """),
        ])
    return


@app.cell
def __(b, cc, cg, influx, tcta):
    import numpy as np
    taxes = influx[['Date_Evenement', 'Id_PRM', 'Formule_Tarifaire_Acheminement', 'Puissance_Souscrite', 'end_date']].copy().set_index('Id_PRM')

    taxes['Puissance_Souscrite'] = taxes['Puissance_Souscrite'].astype(float)
    taxes['j'] = (taxes['end_date'] - taxes['Date_Evenement']).dt.days + 1
    taxes

    def get_tarif(row):
        key = row['Formule_Tarifaire_Acheminement'].replace('BTINF', '')
        if key in b.index:
            return b.at[key, '€/kVA/an']
        else:
            return np.nan

    # On récupére les valeurs de b en fonction de la FTA
    taxes['b'] = taxes.apply(get_tarif, axis=1)

    taxes['turpe_fix_j'] = (cg + cc + taxes['b'] * taxes['Puissance_Souscrite'])/366
    taxes['turpe_fix'] = taxes['turpe_fix_j'] * taxes['j']
    taxes['cta'] = tcta * taxes['turpe_fix']
    taxes
    return get_tarif, np, taxes


@app.cell
def __(taxes):
    taxes['cta'].sum()

    return


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
