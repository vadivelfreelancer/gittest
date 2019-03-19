# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class PappayaProgramme(models.Model):
    _name = 'pappaya.programme'
    
    
    name = fields.Char('Programme Name', size=40)
    # branch_id = fields.Many2one('res.company', string='Branch')
    description = fields.Text(string='Description', size=100)

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Record already exists")

