# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm, ValidationError

class BankNameConfig(models.Model):
    _name = 'bank.name.config'
    _rec_name = 'name'

    name = fields.Char('Bank Name',size=100)
    bank_code = fields.Char('Bank Code',size=15)

    @api.one
    @api.constrains('name','bank_code')
    def _check_bank_name(self):
        if len(self.search([('name', '=', self.name),('bank_code', '=', self.bank_code)])) > 1:
            raise ValidationError('Bank name and code already exists')
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError('Bank Name already exists')
        if len(self.search([('bank_code', '=', self.bank_code)])) > 1:
            raise ValidationError('Bank Code already exists')