import json
from odoo import api, fields, models

class ClientsTable(models.Model):
    _name = "datainterfacetables.client"
    _description = "client"

    name = fields.Char(index=True)
    title = fields.Many2one('res.partner.title')
    parent_id = fields.Many2one('res.partner', string='Related Company', index=True)
    ref = fields.Char(string='Reference', index=True)
    website = fields.Char('Website Link')
    comment = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    employee = fields.Boolean(help="Check this box if this contact is an Employee.")
    function = fields.Char(string='Job Position')
    type = fields.Char( default = 'contact')
    # address fields
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    email = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()
    is_company = fields.Boolean(string='Is a Company', default=False, help="Check if the contact is a company, otherwise it is a person")
    # company_type is only an interface field, do not use it in business logic
    company_type = fields.Selection(string='Company Type', selection=[('person', 'Individual'), ('company', 'Company')])
    company_id = fields.Many2one('res.company', 'Company', index=True)

    def importData(self):
        for record in self:
            obj = {
                'name': record.name,
                'title' : record.title,
                'parent_id': record.partner_id,
                'ref': record.ref,
                'website': record.website,
                'comment': record.comment,
                'active': record.active,
                'employee': record.employee,
                'function': record.function,
                'type': record.type,
                # Address fields
                'street': record.street,
                'street2': record.street2,
                'zip': record.zip,
                'city': record.city,
                'state_id': record.state_id,
                'country_id': record.country_id,
                'email': record.email,
                'phone': record.phone,
                'mobile': record.mobile,
                'is_company': record.is_company,
                'company_type': record.company_type,
                'company_id': record.company_id
            }
            result = self.env['res.partner'].create(obj)
            record.unlink()

    def cronImportData(self):
        result = self.env['datainterfacetables.client'].search([])
        print(result)
        for record in result:
            obj = {
                'name': record.name,
                'title': record.title,
                'parent_id': record.partner_id,
                'ref': record.ref,
                'website': record.website,
                'comment': record.comment,
                'active': record.active,
                'employee': record.employee,
                'function': record.function,
                'type': record.type,
                # Address fields
                'street': record.street,
                'street2': record.street2,
                'zip': record.zip,
                'city': record.city,
                'state_id': record.state_id,
                'country_id': record.country_id,
                'email': record.email,
                'phone': record.phone,
                'mobile': record.mobile,
                'is_company': record.is_company,
                'company_type': record.company_type,
                'company_id': record.company_id
            }
            res = self.env['res.partner'].create(obj)
            record.unlink()

