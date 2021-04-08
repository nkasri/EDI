import json
from odoo import api, fields, models

class LeadTable(models.Model):
    _name = "datainterfacetables.lead"
    _description = "Lead/Opportunity"

    # Customer info
    name = fields.Char('Opportunity', required=True)
    partner_id = fields.Many2one('res.partner')
    partner_name = fields.Char()
    # Address fields
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip')
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", string='State', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country')
    # Web site and others info
    website = fields.Char('Website')
    # Contact info
    contact_name = fields.Char('Contact Name')
    title = fields.Many2one('res.partner.title', string='Title')
    email_from = fields.Char('Email')
    email_cc = fields.Char('Email cc')
    function = fields.Char('Job Position')
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    # Tracking
    referred = fields.Char('Referred By')

    description = fields.Text('Notes')
    type = fields.Char(default='lead')

    # Probability (Opportunity only)
    probability = fields.Float('Probability', group_operator="avg", copy=False)

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

