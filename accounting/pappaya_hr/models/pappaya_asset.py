# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PappayaAssets(models.Model):
    _name = 'pappaya.asset'
    _description = 'Pappaya Assets'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'

    name = fields.Char(string='Name', size=40)
    description = fields.Text(string='Description', size=100)

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")