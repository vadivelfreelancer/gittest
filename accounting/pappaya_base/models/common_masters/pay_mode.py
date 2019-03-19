# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PappayaPaymode(models.Model):
    _name = 'pappaya.paymode'
    _description = 'Pappaya Paymode'
    _order='sequence'

    @api.constrains('is_cheque', 'is_cash', 'is_card','is_challan')
    def check_paymode(self):
        if self.is_cheque and len(self.search([('is_cheque', '=', self.is_cheque)])) > 2:
            raise ValidationError('Cheque/DD already exist..!')
        elif self.is_cash and len(self.search([('is_cash', '=', self.is_cash)])) > 1:
            raise ValidationError('Cash already exist..!')
        elif self.is_card and len(self.search([('is_card', '=', self.is_card)])) > 2:
            raise ValidationError('Card already exist..!')
        elif self.is_challan and len(self.search([('is_challan', '=', self.is_challan)])) > 1:
            raise ValidationError('Challan already exist!')
        elif self.is_paytm and len(self.search([('is_paytm', '=', self.is_paytm)])) > 1:
            raise ValidationError('PayTM already exist!')


    sequence = fields.Integer('Sequence')
    name = fields.Char(string='Name', size=40)
    description = fields.Text(string='Description', size=100)
    is_dependent = fields.Boolean(string='Is Dependent', default=True)
    is_cheque = fields.Boolean(string='Is Cheque?')
    active = fields.Boolean(string='Active', default=True)
    is_card = fields.Boolean('Is Card?')
    is_cash = fields.Boolean('Is Cash?')
    is_challan = fields.Boolean('Is Challan?')
    is_paytm = fields.Boolean('Is PayTM?')
    school_id = fields.Many2one('operating.unit', 'Branch', default=lambda self: self.env.user.default_operating_unit_id)
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    credit_account_id = fields.Many2one('account.account', 'Credit Account')
    debit_account_id = fields.Many2one('account.account', 'Debit Account')
    
    @api.multi
    def unlink(self):
        for rec in self:
            mode_map = self.env['operating.unit'].search([('paymode_ids', 'in', rec.id)])
            if mode_map:
                raise ValidationError('Sorry,You are not authorized to delete record')
        return super(PappayaPaymode, self).unlink()