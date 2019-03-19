# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class PappayaOtherFeeHead(models.Model):
    _name = 'pappaya.other.feehead'
    
    school_id = fields.Many2one('operating.unit', 'School', default=lambda self : self.env.user.default_operating_unit_id)
    name = fields.Char(required=1, string='Name', size=40)
    is_refund = fields.Boolean('Is Refund')
    tax_slno = fields.Char('Tax SL No.',size=50)
    description = fields.Text(string='Description',size=200)
    status = fields.Char('Status')
    is_college = fields.Boolean('Is College')
    is_school = fields.Boolean('Is School')
    is_tax = fields.Boolean('Is Tax')
    subledger_slno = fields.Char('Subledger SL No.',size=50)
    hsnsac_slno = fields.Char('HSN SAC SL No.',size=50)
    can_status = fields.Char('Can Status')

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")