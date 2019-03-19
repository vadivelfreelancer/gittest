# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class PappayaConcessionType(models.Model):
    _name = 'pappaya.concession.type'
    
    school_id = fields.Many2one('operating.unit', 'School', default=lambda self : self.env.user.default_operating_unit_id)
    name = fields.Char(required=1, string='Name', size=40)
    
    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")

