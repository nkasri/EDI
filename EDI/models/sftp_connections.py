from odoo import api, fields, models
import paramiko
import csv
import tarfile
import zipfile
import os
import boto3
import json
import configparser

"""
In this Module:
 - Configure SFTP connections
 - Configure File download from sftp connections
 - Update price list from csv files  
"""


def sftp_conn(hostname, username, password, port=22):
    """Opens SFTP Connection and return an object

    :param hostname: char
        Connection hostname
    :param username: char
        Connection username
    :param password: char
        Connection password
    :param port: Int
        Connection port
    :return: SFTPClient object, referring an SFTP session(channel)
    """
    try:
        transport = paramiko.Transport(hostname, port)
        transport.connect(None, username, password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        return sftp
    except Exception as e:
        print(e)


class edi_sftp_connection(models.Model):
    """
    SFTP connection configuration
    ...
    Attributes
    --------
    :param hostname: char
        Connection hostname
    :param username: char
        Connection username
    :param password: char
         Connection password
    :param supplier: char
         Supplier Name


    """
    _name = "edi.sftp_connection"
    _description = "this model will allow sftp connection to remote servers"
    _rec_name = 'supplier'
    hostname = fields.Char("Hostname", required=True)
    username = fields.Char("Username", required=True)
    password = fields.Char("Password", required=True)
    supplier = fields.Char("Supplier", required=True)

    def sftp_test_conn(self):
        """Takes the object parametres and test the sftp connection
        :return: a wizard(edi.warning_wizard) with Success or Failed message
        """
        self.ensure_one()
        for rec in self:
            hostname = rec.hostname
            password = rec.password
            username = rec.username
            port = 22
            try:
                transport = paramiko.Transport(hostname, port)
                transport.connect(None, username, password)
                res = self.wizard_launcher('SFTP Connection', 'Successful connection', 'success')
                transport.close()
            except Exception as e:
                res = self.wizard_launcher('SFTP Connection', 'connection refused', 'failed')
                return res
            return res

    def wizard_launcher(self, message_title, message, state):
        """Opens a wizard with the message from the parametres

        :param message_title:
        :param message:
        :param state:
        :return: a wizard(edi.warning_wizard) with Success or Failed message
        """
        wizard_exist = self.env['edi.warning_wizard'].sudo().search([('name', '=', state)])
        if wizard_exist:
            wizard_obj = wizard_exist
        else:
            wizard_obj = self.env['edi.warning_wizard'].sudo().create({'name': state,
                                                                       'message': message})
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
    """Warning popup
    """
    _name = "edi.warning_wizard"
    _description = "wizard model"
    name = fields.Char()
    message = fields.Text(string="Connection status", readonly=True, store=True)


class edi_product(models.Model):
    _name = 'edi.product'
    _description = 'Transition table for product prices'
    _rec_name = 'product_id'
    product_id = fields.Char('Product ID')
    NetPrice = fields.Float('Product price')
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
    name = fields.Char(compute='_get_supplier')
    supplier = fields.Char(compute='_get_supplier')
    priceList = fields.Many2one('edi.price_list_config', required=True)
    products = fields.Many2many('edi.product')

    @api.depends('sftp_connection', 'priceList')
    def _get_supplier(self):
        for rec in self:
            if rec.sftp_connection.supplier and rec.priceList.priceListName:
                rec.supplier = rec.sftp_connection.supplier
                rec.name = rec.sftp_connection.supplier + "_" + rec.priceList.priceListName
            else:
                rec.name = ""
                rec.supplier = ""

    def reload(self):
        localPath = self.priceList.priceListNameFinal
        self.process_csv(localPath)

    def send_queue(self, client, queue, product):
        data = json.dumps(product)
        response = queue.send_message(MessageBody=data)

    def process_csv(self, filepath):
        with open(filepath, encoding='cp1252', errors='ignore') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)
            config = configparser.ConfigParser()
            config.read("/mnt/extra-addons/EDI/config.ini")
            client = boto3.resource('sqs',
                                    region_name=config['DEFAULT']['region_name'],
                                    aws_access_key_id=config['DEFAULT']['aws_access_key_id'],
                                    aws_secret_access_key=config['DEFAULT']['aws_secret_access_key'])
            queue = client.get_queue_by_name(QueueName=config['DEFAULT']['QueueName'])
            for row in csv_reader:
                if (len(row)) > 2:
                    try:
                        self.productUpdate(row[int(self.priceList.listFieldConfig.product_code)],
                                           row[int(self.priceList.listFieldConfig.qty)],
                                           row[int(self.priceList.listFieldConfig.price)])
                        message = {'product_code': row[self.priceList.listFieldConfig.product_code],
                                   'qty': row[int(self.priceList.listFieldConfig.qty)],
                                   'price': row[int(self.priceList.listFieldConfig.price)]
                                   }
                    # self.send_queue(client, queue, message)
                    except Exception as e:
                        print(f"product with code: {row[int(self.priceList.listFieldConfig.product_code)]}"
                              f"has wrong value"
                              f"")

    def productUpdate(self, product_ref, qty, price):
        try:
            product_obj = self.env['edi.product'].search([('product_id', '=', product_ref)])
            product = self.env['product.supplierinfo'].search([('product_code', '=', product_ref)])
            if not product_obj:
                product_obj = self.env['edi.product'].sudo().create({'product_id': product_ref,
                                                                     'AvailableQuantity': qty,
                                                                     'NetPrice': price
                                                                     })
                self.write({'products': [(4, product_obj.id)]})
            else:
                product_obj.sudo().write({'AvailableQuantity': qty, 'NetPrice': price})
            if not product:
                product = self.env['product.supplierinfo'].sudo().create(
                    {
                        'product_code': product_ref,
                        'min_qty': qty,
                        'price': price,
                        'name': self.priceList.supplier,
                        'delay': 0,
                        'currency_id': 1
                    })

            else:
                product.sudo().write({'min_qty': qty,
                                      'price': price})
        except Exception as e:
            print(e)
            return product_obj

    def file_type(self, filename):
        filetype = "file"
        if tarfile.is_tarfile(filename):
            filetype = "tar"
        elif zipfile.is_zipfile(filename):
            filetype = "tar"
        return filetype


class edi_upload(models.Model):
    _inherit = 'edi.file_transfer'
    _name = 'edi.file_upload'
    _description = 'file download'

    orders = fields.Many2many('edi.order')


class edi_pricelist_config(models.Model):
    _name = 'edi.price_list_config'
    _description = 'edi model for configuring priceList '

    name = fields.Char(compute="compute_rec_name")
    sftp_conn = fields.Many2one('edi.sftp_connection')
    supplier = fields.Many2one("res.partner")
    priceListName = fields.Char("Price list name")
    priceListNameFinal = fields.Char(compute='compute_priceListName')
    listFields = fields.Char(compute="_get_field", readonly=True)
    listFieldConfig = fields.Many2one('edi.price_list_fields', readonly=True)
    selection = fields.Many2one('edi.selections')

    @api.depends('priceListName')
    def compute_priceListName(self):
        for rec in self:
            rec.get_file()
            if rec.priceListName:
                rec.priceListNameFinal = rec.extract_file(rec.priceListName)
            else:
                rec.priceListNameFinal = ""

    @api.depends('sftp_conn', 'priceListName')
    def compute_rec_name(self):
        for rec in self:
            rec.name = rec.sftp_conn.supplier + "_" + rec.priceListName

    def extract_file(self, file):
        filename = "/mnt/extra-addons/pricelists/" + file
        if tarfile.is_tarfile(filename):
            with tarfile.open(filename) as tf:
                tf.extractall()
            return filename
        elif zipfile.is_zipfile(filename):
            with zipfile.ZipFile(filename, "r") as zf:
                newdir = filename + "dir"
                print(f"that the new folder {newdir}")
                try:
                    os.mkdir(newdir)
                except Exception as e:
                    print(e)
                    print("Folder already exists")
                os.chdir(newdir)
                zf.extractall()
                print(newdir + "/" + file)
                newfile = self.archive_files(filename, 'zip')
                newFilePath = newdir + "/" + newfile[0]
            return newFilePath
        else:
            print('{} is not an accepted archive file'.format(filename))
            return filename

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

    def get_file(self):
        try:
            sftp = sftp_conn(self.sftp_conn.hostname, self.sftp_conn.username,
                             self.sftp_conn.password, 22)
            localPath = "/mnt/extra-addons/pricelists/" + self.priceListName
            sftp.get(self.priceListName, localPath)
            if sftp: sftp.close()
        except Exception as e:
            print(e)

    def _get_field(self):
        list = []
        for rec in self:
            rec.listFields = ""
            if rec.sftp_conn and rec.priceListName:
                selection = rec.env['edi.selections'].create(
                    {'name': rec.sftp_conn.supplier + '_' + rec.priceListName, 'in_use': True})
                rec.write({'selection': selection})
                localPath = rec.priceListNameFinal
                try:
                    with open(localPath, encoding='cp1252', errors='ignore') as csv_file:
                        csv_r = csv.reader(csv_file)
                        data = next(csv_r)
                        i = 0
                        for elem in data:
                            list.append((str(i), elem))
                            field = rec.field_create(elem, str(i), True, selection.id)
                            selection.write({'fields_ids': [(4, field.id)]})
                            i += 1
                        rec.listFields = list
                except Exception as e:
                    print(f"_get_field : {e}")

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


class edi_pricelist_fields(models.Model):
    _name = 'edi.price_list_fields'
    _description = 'edi model for configuring priceList fields '

    name = fields.Char('Configuration fichier', compute='compute_name')
    priceSupplier = fields.Selection(string='Champ Prix Fournisseur', selection=lambda self: self.init())
    product_nameSupplier = fields.Selection(string='Champ Nom fournisseur', selection=lambda self: self.init())
    qtySupplier = fields.Selection(string='Champ quantite fournisseur', selection=lambda self: self.init())
    product_codeSupplier = fields.Selection(string='Reference constructeur', selection=lambda self: self.init())
    product_code = fields.Integer(string="Code produit ordre", compute="save", store=True, readonly=True)
    qty = fields.Integer(string="Code produit quantite", compute="save", store=True, readonly=True)
    price = fields.Integer(string="Code produit prix", compute="save", store=True, readonly=True)
    config = fields.Many2one('edi.price_list_config', readonly=True)
    selection = fields.Many2one('edi.selections')

    def init(self):
        if self.selection or self.env.context.get('selection'):
            if self.selection:
                select_id = self.selection.id
            elif self.env.context.get('selection'):
                select_id = self.env.context.get('selection')
                self.write({'selection': select_id})
            selection = self.env['edi.selections']
            listFields = selection.get_selection_field(select_id)
        else:
            listFields = []
        return listFields

    def edit(self):
        for rec in self:
            vals = {'priceSupplier': rec.priceSupplier,
                    'qtySupplier': rec.qtySupplier,
                    'product_codeSupplier': rec.product_codeSupplier,
                    }
            rec = super(edi_pricelist_fields, self).write(vals)
            return rec

    @api.depends('product_codeSupplier', 'priceSupplier', 'qtySupplier')
    def save(self):
        for rec in self:
            rec.product_code = rec.product_codeSupplier
            rec.price = rec.priceSupplier
            rec.qty = rec.qtySupplier

    @api.depends('config')
    def compute_name(self):
        for rec in self:
            if rec.config.supplier.name and rec.config.priceListName:
                rec.name = rec.config.supplier.name + "_" + rec.config.priceListName


class edi_schedual_update(models.Model):
    _name = 'edi.schedual_update'
    _description = 'Class to schedual the price lists updates'
    hour = fields.Integer('Heure')
    samedi = fields.Boolean('Samedi')
    Dimanche = fields.Boolean('Dimanche')
    Lundi = fields.Boolean('Lundi')
    Mardi = fields.Boolean('Mardi')
    Mercredi= fields.Boolean('Mercredi')
    Jeudi = fields.Boolean('Jeudi')
    Vendredi = fields.Boolean('Vendredi')
