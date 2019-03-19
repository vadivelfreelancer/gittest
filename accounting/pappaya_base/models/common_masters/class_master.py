# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class PappayaClass(models.Model):
    _name = 'pappaya.class'
    
    name = fields.Char(string='Name', size=40)
    description = fields.Text(string='Description', size=100)
    branch_id = fields.Many2one('operating.unit', string='Branch')

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")
