import json
from odoo import api, fields, models, _


class OrderTable(models.Model):
    _name = "datainterfacetables.order"
    _description = "Order"

    idTekkeys = fields.Char(string='Tekkeys Order ID')
    number = fields.Integer(string='Number')
    dateTekkeys = fields.Date(string='Tekkeys Date')
    orderLines = fields.One2many('datainterfacetables.order.line', 'orderId')
    totals = fields.Float(string='totals')
    InvoiceAdresse = fields.Char(string='Invoice Address')
    shippingAdresse = fields.Char(string='Shipping Address')
    shippingFees = fields.Float(string='shipping Fees')

    def acceptOrder(self, data):
        order = {
            'idTekkeys': data['idTekkeys'],
            'number': data['number'],
            'dateTekkeys': data['dateTekkeys'],
            'totals': data['totals'],
            'InvoiceAdresse': data['InvoiceAdresse'],
            'shippingAdresse': data['shippingAdresse'],
            'shippingFees': data['shippingFees'],
        }
        orderID = self.create(order)
        print(orderID)

        lines = data['orderLines']
        linesIds = []
        for line in lines:
            objLine = {
                'orderId': orderID.id,
                'reference': line['reference'],
                'qte': line['qte'],
                'salePrice': line['salePrice']
            }
            lineID = self.env['datainterfacetables.order.line'].create(objLine)
            linesIds.append(lineID.id)

        print(linesIds)
        odooOrder = self.env['datainterfacetables.order'].search([('id', '=', orderID.id)])
        odooOrder.write({'orderLines': linesIds})


    def importData(self):
        for record in self:
            obj = {
                'idTekkeys': record.name,
                'number': record.partner_id,
                'dateTekkeys': record.partner_name,
                'orderLines': record.street,
                'totals': record.street2,
                'InvoiceAdresse': record.zip,
                'shippingAdresse': record.city,
                'shippingFees': record.state_id,
            }
            result = self.env['sale.order'].create(obj)
            record.unlink()

    def cronImportData(self):
        result = self.env['datainterfacetables.order'].search([])
        print(result)
        for record in result:
            obj = {
                'idTekkeys': record.name,
                'number': record.partner_id,
                'dateTekkeys': record.partner_name,
                'orderLines': record.street,
                'totals': record.street2,
                'InvoiceAdresse': record.zip,
                'shippingAdresse': record.city,
                'shippingFees': record.state_id,
            }
            res = self.env[sale.order].create(obj)
            record.unlink()


class OrderLineTable(models.Model):
    _name = "datainterfacetables.order.line"
    _description = "Order line"

    orderId = fields.Many2one('datainterfacetables.order')
    reference = fields.Char(string='Product reference')
    qte = fields.Float(string='Quantity')
    salePrice = fields.Float(string='Sale price')
