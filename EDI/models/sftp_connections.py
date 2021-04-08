from odoo import api, fields, models
import paramiko
from paramiko import AuthenticationException


class edi_sftp_connection(models.Model):
    _name = "edi.sftp_connection"
    _desc = "this model will allow sftp connection to remote servers"

    hostname = fields.Char("Hostname", required=True)
    username = fields.Char("Username", required=True)
    password = fields.Char("Password", required=True)
    supplier = fields.Char("Supplier", required=True)

    def sftp_test_conn(self):
        self.ensure_one()
        res = {}
        for rec in self:
            hostname = rec.hostname
            password = rec.password
            username = rec.username
            port = 22
            refused_msg = self.env['edi.warning_wizard'].sudo().create({'message': 'connection refused'})
            success_msg = self.env['edi.warning_wizard'].sudo().create({'message': 'successfull connection'})
            try:
                transport = paramiko.Transport(hostname, port)
                transport.connect(None, username, password)
                res = {

                    'name': 'warning.wizard',

                    'type': 'ir.actions.act_window',

                    'res_model': 'edi.warning_wizard',

                    'view_mode': 'form',

                    'view_type': 'form',

                    'target': 'new',

                    'res_id': success_msg.id
                           }
                transport.close()
            except Exception as e:
                print(f"it's gotten here {e}")
                res = {
                    'name': 'SFTP Connection',

                    'type': 'ir.actions.act_window',

                    'res_model': 'edi.warning_wizard',

                    'view_mode': 'form',

                    'view_type': 'form',

                    'target': 'new',

                    'res_id': refused_msg.id
                }
                return res
            return res


class warning_popups(models.TransientModel):
    _name = "edi.warning_wizard"
    _desc = "wizard model"

    message = fields.Text(string="Connection status", readonly=True, store=True)
