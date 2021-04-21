import json
from odoo import api, fields, models, _


class OrderTable(models.Model):
    _name = "datainterfacetables.order"
    _description = "Order"

    idTekkeys = fields.Char(string='Tekkeys Order ID')
    clientName = fields.Char(string="Name")
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
            'clientName': data['clientName'],
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
            partner_id = self.env['res.partner'].search([('name', '=', record['clientName'])])
            order = {
                'client_order_ref': record['idTekkeys'],
                'partner_id': partner_id.id,
                'date_order': record['dateTekkeys'],
                'amount_total': record['totals'],
            }
            orderID = self.env['sale.order'].create(order)
            record.unlink()
            print(orderID.id)

            lines = self.env['datainterfacetables.order.line'].search([('orderId', '=', record['id'])])
            linesIds = []
            for line in lines:
                productID = self.env['product.product'].search([('default_code', '=', line['reference'])])
                objLine = {
                    'order_id': orderID.id,
                    'product_id': productID.id,
                    'product_uom_qty': line['qte'],
                    'price_unit': line['salePrice']
                }
                lineID = self.env['sale.order.line'].create(objLine)
                line.unlink()
                linesIds.append(lineID.id)

            odooOrder = self.env['sale.order'].search([('id', '=', orderID.id)])
            odooOrder.write({'order_line': linesIds})

    def cronImportData(self):
        for record in self:
            partner_id = self.env['res.partner'].search([('name', '=', record['clientName'])])
            order = {
                'client_order_ref': record['idTekkeys'],
                'partner_id': partner_id.id,
                'date_order': record['dateTekkeys'],
                'amount_total': record['totals'],
            }
            orderID = self.env['sale.order'].create(order)
            record.unlink()
            print(orderID.id)

            lines = self.env['datainterfacetables.order.line'].search([('orderId', '=', record['id'])])
            linesIds = []
            for line in lines:
                productID = self.env['product.product'].search([('default_code', '=', line['reference'])])
                objLine = {
                    'order_id': orderID.id,
                    'product_id': productID.id,
                    'product_uom_qty': line['qte'],
                    'price_unit': line['salePrice']
                }
                lineID = self.env['sale.order.line'].create(objLine)
                line.unlink()
                linesIds.append(lineID.id)

            odooOrder = self.env['sale.order'].search([('id', '=', orderID.id)])
            odooOrder.write({'order_line': linesIds})


class OrderLineTable(models.Model):
    _name = "datainterfacetables.order.line"
    _description = "Order line"

    orderId = fields.Many2one('datainterfacetables.order')
    reference = fields.Char(string='Product reference')
    qte = fields.Float(string='Quantity')
    salePrice = fields.Float(string='Sale price')
