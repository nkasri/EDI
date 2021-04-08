# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class generique_addon(models.Model):
#     _name = 'generique_addon.generique_addon'
#     _description = 'generique_addon.generique_addon'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
