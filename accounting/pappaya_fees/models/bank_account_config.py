# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm, ValidationError
import re
from datetime import datetime

class BankAccountConfig(models.Model):
    _name = 'bank.account.config'
    _rec_name = 'display_name'


    school_ids = fields.Many2many('operating.unit', 'school_bank_account_rel', 'structure_id', 'school_id', string='Branch')
    bank_id = fields.Many2one('bank.name.config', string='Bank Name')
    name_on_bank = fields.Char(string='Name as on Bank',size=100)
    account_number = fields.Char(string='Account Number', size=16)
    ifsc_code = fields.Char(string='IFSC Code', size=11)
    bank_address = fields.Text(string='Bank Address',size=200)
    created_on = fields.Datetime(string='Created On', default=lambda self: fields.Datetime.now())
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    display_name = fields.Char('Display Name', compute='compute_display_name', store=True,size=100)

    @api.one
    @api.constrains('account_number')
    def _check_bank_account(self):
        for record in self:
            if len(self.search([('account_number','=',self.account_number),('school_ids','in',self.school_ids.ids)])) > 1:
                raise ValidationError('Account number must be unique!')
    
    @api.depends('name_on_bank','bank_id','account_number')
    def compute_display_name(self):
        if self.name_on_bank and self.bank_id and self.account_number:
            self.display_name = str(self.name_on_bank) + ' - ' + str(self.bank_id.bank_code or '') + ' (' + str(self.account_number) + ')'

    #~ @api.onchange('society_id')
    #~ def onchange_society(self):
        #~ if  self.society_id:
            #~ self.school_ids = None
            #~ self.bank_id = None
            #~ self.name_on_bank = None
            #~ self.account_number = None
            #~ self.ifsc_code = None
            #~ self.bank_address = None

    #~ @api.onchange('school_ids')
    #~ def onchange_school(self):
        #~ if self.school_ids:
            #~ self.bank_id = None
            #~ self.name_on_bank = None
            #~ self.account_number = None
            #~ self.ifsc_code = None
            #~ self.bank_address = None

    #~ @api.onchange('bank_id')
    #~ def onchange_bank(self):
        #~ if self.bank_id:
            #~ self.name_on_bank = None
            #~ self.account_number = None
            #~ self.ifsc_code = None
            #~ self.bank_address = None
