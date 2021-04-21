from odoo import api, fields, models
import paramiko
from paramiko import AuthenticationException
import csv
import tarfile
import zipfile
import os


def sftp_conn(hostname, username, password, port=22):
    try:
        transport = paramiko.Transport(hostname, port)
        transport.connect(None, username, password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        return sftp
    except Exception as e:
        print(e)


class edi_sftp_connection(models.Model):
    _name = "edi.sftp_connection"
    _description = "this model will allow sftp connection to remote servers"
    _rec_name = 'supplier'
    hostname = fields.Char("Hostname", required=True)
    username = fields.Char("Username", required=True)
    password = fields.Char("Password", required=True)
    supplier = fields.Char("Supplier", required=True)

    def sftp_test_conn(self):
        self.ensure_one()
        for rec in self:
            hostname = rec.hostname
            password = rec.password
            username = rec.username
            port = 22
            try:
                transport = paramiko.Transport(hostname, port)
                transport.connect(None, username, password)
                res = self.wizard_launcher('SFTP Connection', 'Successful connection')
                transport.close()
            except Exception as e:
                res = self.wizard_launcher('SFTP Connection', 'connection refused')
                return res
            return res

    def wizard_launcher(self, message_title, message):
        wizard_obj = self.env['edi.warning_wizard'].sudo().create({'message': message})
        res = {'name': message_title,

               'type': 'ir.actions.act_window',

               'res_model': 'edi.warning_wizard',

               'view_mode': 'form',

               'view_type': 'form',

               'target': 'new',

               'res_id': wizard_obj.id

               }
        return res


class warning_popups(models.TransientModel):
    _name = "edi.warning_wizard"
    _description = "wizard model"

    message = fields.Text(string="Connection status", readonly=True, store=True)


class edi_pricelist_config_wizard(models.TransientModel):
    _name = "edi.price_list_fields"
    _description = "wizard model"

    message = fields.Text(string="Connection status", readonly=True, store=True)


class edi_product(models.Model):
    _name = 'edi.product'
    _description = 'Transition table for product prices'
    _rec_name = 'product_id'
    product_id = fields.Integer('Product ID')
    NetPrice = fields.Integer('Product price')
    AvailableQuantity = fields.Integer('Product available quantity')


class edi_order(models.Model):
    _name = 'edi.order'
    _description = 'Temporary order model for tests'

    name = fields.Char('Order ref')
    path = fields.Char('Path')


class edi_file_transfer(models.Model):
    _name = 'edi.file_transfer'
    _description = 'model containing'

    sftp_connection = fields.Many2one('edi.sftp_connection')


class edi_download(models.Model):
    _inherit = 'edi.file_transfer'
    _name = 'edi.file_download'
    _description = 'file download'

    supplier = fields.Char(compute='_get_supplier')
    priceList = fields.Many2one('edi.price_list_config', required=True)
    products = fields.Many2many('edi.product')

    @api.depends('sftp_connection')
    def _get_supplier(self):
        for rec in self:
            rec.supplier = rec.sftp_connection.supplier

    def reload(self):
        localpath = "/mnt/extra-addons/pricelists/" + self.priceList.priceListName
        self.process_csv(localpath)

    # def reload(self):
    #     hostname = self.sftp_connection.hostname
    #     password = self.sftp_connection.password
    #     username = self.sftp_connection.username
    #     port = 22
    #     try:
    #         transport = paramiko.Transport(hostname, port)
    #         transport.connect(None, username, password)
    #         sftp = paramiko.SFTPClient.from_transport(transport)
    #         files = sftp.listdir('.')
    #         for file in files:
    #             localpath = "/mnt/extra-addons/pricelists/" + file
    #             sftp.get(file, localpath)
    #             print("before file type")
    #             if self.file_type(localpath) == "file":
    #                 print("inside if file")
    #                 self.process_csv(localpath)
    #             else:
    #                 print("here in the extract")
    #                 newfiles = self.extract_file(localpath)
    #                 print(newfiles)
    #                 self.process_csv(newfiles[0])
    #         if sftp: sftp.close()
    #         if transport: transport.close()
    #     except Exception as e:
    #         print(e)

    def process_csv(self, filepath):
        with open(filepath) as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)
            for row in csv_reader:
                if (len(row)) > 2:
                    # self.productUpdate(row[0], row[2], row[1])
                    print(f"code product {row[int(self.priceList.listFieldConfig.product_codeSupplier)]}")
                    print(f"qtysup {row[int(self.priceList.listFieldConfig.qtySupplier)]}")
                    print(f"pricelsitconfig id {self.priceList}")
                    # print(f"price product {self.priceList.listFieldConfig._fields['priceSupplier'].selection)")
                    listConfig = self.env['edi.price_list_config'].search([('id', '=', self.priceList.id)])
                    # print(listConfig.priceSupplier)
                    # print(listConfig.qtySupplier)
                    print(listConfig)
                    self.productUpdate(row[int(self.priceList.listFieldConfig.product_codeSupplier)],
                                       row[int(self.priceList.listFieldConfig.qtySupplier)],
                                       row[int(self.priceList.listFieldConfig.priceSupplier)])

    def productUpdate(self, product_ref, qty, price):
        product_obj = self.env['edi.product'].search([('product_id', '=', product_ref)])
        if not product_obj:
            product_obj = self.env['edi.product'].sudo().create({'product_id': product_ref,
                                                                 'AvailableQuantity': qty,
                                                                 'NetPrice': price
                                                                 })
            self.write({'products': [(4, product_obj.id)]})
        else:
            product_obj.sudo().write({'AvailableQuantity': qty, 'NetPrice': price})
        return product_obj

    def extract_file(self, filename):
        if tarfile.is_tarfile(filename):
            with tarfile.open(filename) as tf:
                tf.extractall()
            return filename
        elif zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, "r") as zf:
                currentdir = os.getcwd()
                newdir = currentdir + "/dir" + filename
                print(newdir)
                try:
                    os.mkdir(newdir)
                except Exception as e:
                    print("Folder already exists")
                os.chdir(newdir)
                zf.extractall()
                print(newdir + "/" + filename)
                newfile = self.archive_files(newdir + "/" + filename)
            return newfile
        else:
            print('{} is not an accepted archive file'.format(filename))

    def extract_file_multiple(self, filename):
        if tarfile.is_tarfile(filename):
            with tarfile.open(filename) as tf:
                tf.extractall()
            return filename
        elif zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, "r") as zf:
                currentdir = os.getcwd()
                newdir = currentdir + filename + "/dir"
                try:
                    os.mkdir(newdir)
                except Exception as e:
                    print("Folder already exists")
                os.chdir(newdir)
                zf.extractall()
                archive_files = self.archive_files(newdir + "/" + filename)
                newfiles = []
                for name in archive_files:
                    newfiles.append(newdir + "/" + name)
            return newfiles
        else:
            print('{} is not an accepted archive file'.format(filename))

    def file_type(self, filename):
        filetype = "file"
        if tarfile.is_tarfile(filename):
            filetype = "tar"
        elif zipfile.is_zipfile(filename):
            filetype = "tar"
        return filetype

    def archive_files(self, filename, type):
        files = []
        if type == "tar":
            f = tarfile.open(filename)
            for info in f:
                files.append(info.name)
        else:
            f = zipfile.ZipFile(filename)
            for name in f.namelist():
                files.append(name)
        return files


class edi_upload(models.Model):
    _inherit = 'edi.file_transfer'
    _name = 'edi.file_upload'
    _description = 'file download'

    orders = fields.Many2many('edi.order')


class edi_pricelist_config(models.Model):
    _name = 'edi.price_list_config'
    _description = 'edi model for configuring priceList '

    sftp_conn = fields.Many2one('edi.sftp_connection')
    supplier = fields.Many2one("res.partner")
    priceListName = fields.Char("Price list name")
    listFields = fields.Char(compute="_get_field")
    listFieldConfig = fields.Many2one('edi.price_list_fields')
    selection = fields.Many2one('edi.selections')

    # def _get_field(self):
    #     list = []
    #     for rec in self:
    #         rec.listFields = ""
    #         if rec.sftp_conn and rec.priceListName:
    #             hostname = rec.sftp_conn.hostname
    #             password = rec.sftp_conn.password
    #             username = rec.sftp_conn.username
    #             sftp = sftp_conn(hostname, password, username)
    #             selection = self.env['edi.selections'].create({'name': 'rec.priceListName', 'in_use': True})
    #             self.write({'selection': selection})
    #             print(f"in the parent method:{self.selection}")
    #             if sftp:
    #                 localPath = "/mnt/extra-addons/pricelists/" + rec.priceListName
    #                 try:
    #                     sftp.get(rec.priceListName, localPath)
    #                     with open(localPath) as csv_file:
    #                         csv_r = csv.reader(csv_file)
    #                         data = next(csv_r)
    #                         i = 0
    #                         for elem in data:
    #                             list.append((str(i), elem))
    #                             field = self.field_create(elem, str(i), True, selection.id)
    #                             selection.write({'fields_ids': [(4, field.id)]})
    #                             i += 1
    #                         rec.listFields = list
    #                     if sftp: sftp.close()
    #                 except Exception as e:
    #                     print(e)

    def _get_field(self):
        list = []
        for rec in self:
            rec.listFields = ""
            if rec.sftp_conn and rec.priceListName:
                selection = self.env['edi.selections'].create({'name': 'rec.priceListName', 'in_use': True})
                self.write({'selection': selection})
                print(f"in the parent method:{self.selection}")
                localPath = "/mnt/extra-addons/pricelists/" + rec.priceListName
                try:
                    with open(localPath) as csv_file:
                        csv_r = csv.reader(csv_file)
                        data = next(csv_r)
                        i = 0
                        for elem in data:
                            list.append((str(i)+"a", elem))
                            field = self.field_create(elem, str(i)+"a", True, selection.id)
                            selection.write({'fields_ids': [(4, field.id)]})
                            i += 1
                        rec.listFields = list
                except Exception as e:
                    print(e)

    def field_create(self, name, value, in_use, selection_id):
        obj = self.env['edi.selections.fields'].create({
            'name': name,
            'value': value,
            'in_use': in_use,
            'selection_id': selection_id,
        })
        return obj

    def return_view(self):
        if self.listFieldConfig:
            wizard_obj = self.listFieldConfig
        else:
            wizard_obj = self.env['edi.price_list_fields'].create({'config': self.id})
        self.write({'listFieldConfig': wizard_obj.id})
        ctx = self.env.context.copy()
        print(self.selection)
        ctx.update({'selection': self.selection.id})
        wizard_obj.with_context(ctx).init()
        return {
            'name': 'Fields configuration',

            'type': 'ir.actions.act_window',

            'res_model': 'edi.price_list_fields',

            'view_mode': 'form',

            'view_type': 'form',

            'target': 'new',

            'res_id': wizard_obj.id,

            'context': ctx

        }


"""
    @api.depends('listFields')
    def _get_fields(self):

        select = self.listFields

        return select
"""


class edi_pricelist_fields(models.Model):
    _name = 'edi.price_list_fields'
    _description = 'edi model for configuring priceList fields '

    priceSupplier = fields.Selection(string='Supplier price', selection=lambda self: self.init())
    product_nameSupplier = fields.Selection(string='Supplier product name', selection=lambda self: self.init())
    qtySupplier = fields.Selection(string='Supplier quantity', selection=lambda self: self.init())
    product_codeSupplier = fields.Selection(string='Supplier product code', selection=lambda self: self.init())
    config = fields.Many2one('edi.price_list_config', readonly=True)
    selection = fields.Many2one('edi.selections')

    def init(self):
        # if self.env.context.get('selection', False):
        if self.selection:
            select_id = self.selection.id
            print(f"this the selection found: {self.selection.id}")
        else:
            print("get Context of Wizard HERE", self.env.context.get('selection'))
            select_id = self.env.context.get('selection')
            self.write({'selection': select_id})
        selection = self.env['edi.selections']
        listFields = selection.get_selection_field(select_id)
        return listFields

    def edit(self):
        for rec in self:
            vals = {'priceSupplier': rec.priceSupplier,
                    'qtySupplier': rec.qtySupplier,
                    'product_codeSupplier': rec.product_codeSupplier,
                    }
            print(f"this fields: {rec.priceSupplier}")
            rec = super(edi_pricelist_fields, self).write(vals)
            return rec
