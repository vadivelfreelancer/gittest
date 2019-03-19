# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class PappayaVc(models.Model):
    _name = 'pappaya.vc'
    
    school_id = fields.Many2one('operating.unit', 'School', default=lambda self : self.env.user.default_operating_unit_id)
    name = fields.Char(required=1, string='Name', size=40)
    description = fields.Text(string='Description',size=200)
    emp_slno = fields.Char('Emp SL No.')
    unique_no = fields.Char('Unique No.')
    ic_name = fields.Char('IC Name')
    email = fields.Char('Email')
    mobile = fields.Char('Mobile No.')
    user_slno = fields.Char('User SL No.')

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")