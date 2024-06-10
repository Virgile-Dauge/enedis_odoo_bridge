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

# Fonction pour obtenir la date du 5 du mois suivant
def get_next_fifth():
    today = datetime.datetime.today()
    # Si c'est décembre, on passe à janvier de l'année suivante
    if today.month == 12:
        next_fifth = today.replace(year=today.year + 1, month=1, day=5)
    else:
        next_fifth = today.replace(month=today.month + 1, day=5)
    return next_fifth
def get_lines(record):
    return [{
            'product_id': line.product_id.id,
            'quantity': line.product_uom_qty,
            #'price_unit': line.price_unit,
            #'name': line.name,
            #'account_id': line.product_id.property_account_income_id.id or line.product_id.categ_id.property_account_income_categ_id.id,
        } for line in record.order_line]

def add_create_cmd(lines):
    return [Command.create(line) for line in lines]

def setup_invoice(record):
    return {
        'partner_id': record.partner_id.id,
        'move_type': 'out_invoice',  # Type de facture (facture client)
        'invoice_date': datetime.datetime.today().replace(day=5),
        'invoice_origin': record.name,
        'invoice_payment_term_id': record.payment_term_id.id,
        'invoice_line_ids': invoice_lines,
    }
    
for record in records:
    if record.state != 'sale' or record.x_invoicing_state != 'paid':
        continue
    
    invoice_vals = record._create_invoices()
    
    record.write({
            'next_invoice_date': get_next_fifth(),
            'x_invoicing_state': 'draft',
    })
