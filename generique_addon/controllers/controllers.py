# -*- coding: utf-8 -*-
# from odoo import http


# class GeneriqueAddon(http.Controller):
#     @http.route('/generique_addon/generique_addon/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/generique_addon/generique_addon/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('generique_addon.listing', {
#             'root': '/generique_addon/generique_addon',
#             'objects': http.request.env['generique_addon.generique_addon'].search([]),
#         })

#     @http.route('/generique_addon/generique_addon/objects/<model("generique_addon.generique_addon"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('generique_addon.object', {
#             'object': obj
#         })
