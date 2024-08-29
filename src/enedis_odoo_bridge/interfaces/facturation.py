import marimo

__generated_with = "0.8.4"
app = marimo.App(width="medium", app_title="Facturation")


@app.cell(hide_code=True)
async def enedis_embeding():
    import marimo as mo

    from extract_enedis_data import app
    # execute the notebook
    with mo.status.spinner(title="Extraction des données Enedis...") as _spinner:
      eed = await app.embed()
      _spinner.update("Extraction terminée")

    mo.accordion(
        {"Détails de l'extraction des données enedis": eed.output}
    )
    return app, eed, mo


@app.cell
def __(eed):
    consos = eed.defs['taxes']
    env = eed.defs['env']
    consos
    return consos, env


@app.cell
def __(consos):
    _missing_data = consos[(consos['missing_data'] == True) & (consos['lisse'] == False)]
    _missing_data.dropna(axis=1, how='all')
    return


@app.cell(hide_code=True)
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
    from xmlrpc.client import ProtocolError

    try:
        _draft_orders_request = odoo.search_read('sale.order', filters=[[['state', '=', 'sale'], ['x_invoicing_state', '=', 'draft']]], fields=['id', 'x_pdl', 'invoice_ids', 'x_lisse', 'x_puissance_souscrite'])
    except ProtocolError as e:
        if e.errcode == 302:
            _stop_msg = mo.callout(mo.md(
                f"""
                ## ⚠ Problème de redirection (302) lors de la connexion à [{odoo.url}]({odoo.url}web#action=437&model=sale.order&view_type=kanban). ⚠ 
                S'il s'agit de la base de test, elle n'est probablement plus en ligne.
                """), kind='warn')
            mo.stop(True, _stop_msg)
        else:
            raise

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
    return ProtocolError, draft_orders, subs_to_display


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
    #draft_invoices.reset_index(inplace=True)

    _merged = draft_orders.merge(draft_invoices[['account.move_id', 'invoice_line_ids']], left_on='move_id', right_on='account.move_id', how='left')

    #_merged.set_index('x_pdl')
    odoo_data = odoo.add_cat_fields(_merged, [])#.drop(columns=['level_0', 'index'])#.set_index('x_pdl', drop=True)
    return draft_invoices, odoo_data


@app.cell
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

        Il faut ajouter aux données Odoo les données suivantes, issues d'Enedis : 

        `['HP', 'HC', 'BASE', 'j', 'missing_data', 'd_date', 'f_date', 'Type_Compteur', 'Num_Serie', 'depannage', 'pdl', 'turpe_fix', 'turpe_var']`
        """
    )
    return


@app.cell(hide_code=True)
def __(consos, odoo_data):
    _required_cols = ['HP', 'HC', 'BASE', 'j', 'missing_data', 'd_date', 'f_date', 'Type_Compteur', 'Num_Serie', 'depannage', 'pdl', 'turpe_fix', 'turpe_var']
    merged_data = odoo_data.merge(consos[_required_cols], left_on='x_pdl', right_on='pdl', how='left')
    merged_data
    return merged_data,


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


@app.cell(hide_code=True)
def maj_odoo(eed, merged_data, mo, odoo, red_button):
    mo.stop(not red_button.value)

    # Préparation des données 
    merged_data['update_dates'] = merged_data['j'] != (eed.defs['end_date_picker'].value - eed.defs['start_date_picker'].value).days + 1

    odoo.update_draft_invoices(merged_data.rename(columns={'BASE': 'Base',
                                                           'j': 'subscription_days',
                                                           'missing_data': 'not_enough_data',
                                                           'd_date': 'start_date',
                                                           'f_date': 'end_date'}))
    return


if __name__ == "__main__":
    app.run()
