# Available variables:
#  - env: environment on which the action is triggered
#  - model: model of the record on which the action is triggered; is a void recordset
#  - record: record on which the action is triggered; may be void
#  - records: recordset of all records on which the action is triggered in multi-mode; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - float_compare: utility function to compare floats based on specific precision
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - _logger: _logger.info(message): logger to emit messages in server logs
#  - UserError: exception class for raising user-facing warning messages
#  - Command: x2many commands namespace
# To return an action, assign: action = {...}
for record in records:
    #record.write({'x_studio_stage_id': 5, 'x_active': False})
    

    # Créer le Contact
    partner = env['res.partner'].create({'name': record.x_name, 
                                         'phone': record.x_telephone,
                                         'email': record.x_email,
                                         'contact_address': record.x_adresse
    })
    
    if record.x_iban:
        # Créer le compte en banque
        bank = env['res.partner.bank'].create({'partner_id': partner.id, 'acc_number': record.x_iban})
        
        # Créer le SEPA
        sepa = env['sdd.mandate'].create({'partner_id': partner.id, 'partner_bank_id': bank.id, 
                                          'start_date': datetime.date.today(), 'state': 'active',
        })
    # Créer l'abonnement
    start_date = datetime.date.today().replace(day=1)
    
    order_dict = {'partner_id': partner.id,
                  'x_cotitulaires': record.x_cotitulaires,
                  'x_puissance_souscrite': record.x_puissance_souscrite,
                  'x_pdl': record.x_pdl,
                  'x_lisse': record.x_lisse,
                  'x_adresse_pdl': record.x_adresse,
                  'x_date_validation_formulaire': record.x_date_soumission_form,
                  'start_date': start_date,}
                  
    option_tarifaire = 'Base' if record.x_option_tarifaire == 'base' else 'HP/HC'
    modele_devis_name = f'Option tarifaire {option_tarifaire} {record.x_puissance_souscrite}kVA'
    
    modele_devis = env['sale.order.template'].search([('name', '=', modele_devis_name)])
    if modele_devis:
        order_dict['sale_order_template_id'] = modele_devis[0].id
    order = env['sale.order'].create(order_dict)
    if modele_devis:
        for line in modele_devis[0].sale_order_template_line_ids:
            order.order_line.create({
                'order_id': order.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom_id.id,
                'name': line.name,
            })


