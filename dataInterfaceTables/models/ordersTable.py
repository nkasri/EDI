import json
from odoo import api, fields, models, _

class OrderTable(models.Model):
    _name = "datainterfacetables.order"
    _description = "Order"

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    origin = fields.Char(string='Source Document', help="Reference of the document that generated this sales order request.")
    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    reference = fields.Char(string='Payment Ref.', copy=False, help='The payment communication of this sale order.')
    state = fields.Char('draft')
    date_order = fields.Datetime(default=fields.Datetime.now, help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.")
    create_date = fields.Datetime(string='Creation Date', readonly=True, index=True, help="Date on which sales order is created.")

    user_id = fields.Many2one('res.users', string='Salesperson', index=True, tracking=2, default=lambda self: self.env.user, domain=lambda self: [('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)])
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, tracking=1, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', readonly=True, required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]}, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]}, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )

    currency_id = fields.Many2one(related='pricelist_id.currency_id', depends=["pricelist_id"], store=True)

    order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True,
                                 auto_join=True)

    invoice_status = fields.Char(default='to invoice')

    note = fields.Text('Terms and conditions')

    amount_untaxed = fields.Monetary(string='Untaxed Amount')
    amount_by_group = fields.Binary(string="Tax amount by group")
    amount_tax = fields.Monetary(string='Taxes')
    amount_total = fields.Monetary(string='Total')
    currency_rate = fields.Float("Currency Rate")

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    amount_undiscounted = fields.Float('Amount Before Discount', compute='_compute_amount_undiscounted', digits=0)


    def importData(self):
        for record in self:
            obj = {
                'name': record.name,
                'partner_id' : record.partner_id,
                'partner_name': record.partner_name,
                # Address fields
                'street': record.street,
                'street2': record.street2,
                'zip': record.zip,
                'city': record.city,
                'state_id': record.state_id,
                'country_id': record.country_id,
                # Web site and others info
                'website': record.website,
                # Contact info
                'contact_name': record.contact_name,
                'title': record.title,
                'email_from': record.email_from,
                'email_cc': record.email_cc,
                'function': record.function,
                'phone': record.phone,
                'mobile': record.mobile,
                # Tracking
                'referred': record.referred,

                'description': record.description,
                'type': record.type
            }
            result = self.env['crm.lead'].create(obj)
            record.unlink()

    def cronImportData(self):
        result = self.env['datainterfacetables.lead'].search([])
        print(result)
        for record in result:
            obj = {
                'name': record.name,
                'partner_id': record.partner_id,
                'partner_name': record.partner_name,
                # Address fields
                'street': record.street,
                'street2': record.street2,
                'zip': record.zip,
                'city': record.city,
                'state_id': record.state_id,
                'country_id': record.country_id,
                # Web site and others info
                'website': record.website,
                # Contact info
                'contact_name': record.contact_name,
                'title': record.title,
                'email_from': record.email_from,
                'email_cc': record.email_cc,
                'function': record.function,
                'phone': record.phone,
                'mobile': record.mobile,
                # Tracking
                'referred': record.referred,
                'description': record.description,
                'type': record.type
            }
            res = self.env['crm.lead'].create(obj)
            record.unlink()


class OrderTable(models.Model):
    _name = "datainterfacetables.order.line"
    _description = "Order line"

    order_id = fields.Many2one('sale.order', string='Order Reference', required=True, ondelete='cascade', index=True,  copy=False)
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    invoice_status = fields.Char('to invoice')
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    price_subtotal = fields.Monetary(string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(string='Total', readonly=True, store=True)

    price_reduce = fields.Float(string='Price Reduce', digits='Product Price', readonly=True, store=True)
    price_reduce_taxinc = fields.Monetary(string='Price Reduce Tax inc', readonly=True, store=True)
    price_reduce_taxexcl = fields.Monetary(string='Price Reduce Tax excl', readonly=True, store=True)

    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)

    product_id = fields.Many2one('product.product', string='Product', domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    product_uom_readonly = fields.Boolean()

    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id.currency_id'], store=True,
                                  string='Currency', readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True, index=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer', readonly=False)
