from odoo import api, fields, models


class Selections(models.Model):
    _name = 'edi.selections'
    name = fields.Char(string='Name', required=True)
    usage = fields.Char(string='Description')
    in_use = fields.Boolean(string='Active', default=True)
    fields_ids = fields.One2many('edi.selections.fields', 'selection_id')

    @api.model
    def get_selection_field(self, selection_id):
        selection = self.search([('id', '=', selection_id)])
        selection_list = list()
        for data in selection.fields_ids:
            if data.in_use:
                selection_list.append((data.value, data.name))
        return selection_list


class SelectionsFields(models.Model):
    _name = 'edi.selections.fields'
    _order = 'value asc'
    name = fields.Char(string='Option', required=True)
    value = fields.Char(string='Value', required=True)
    in_use = fields.Boolean(string='Active', default=True)
    selection_id = fields.Many2one('edi.selections', ondelete='cascade', index=True)
