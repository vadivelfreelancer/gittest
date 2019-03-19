# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm, ValidationError
import re
import time
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class bank_challan_transaction(models.Model):
    _name = 'bank.challan.transaction'
    _rec_name='ibank_transaction_id'

    ibank_transaction_id = fields.Char('IBANK TRANSACTION ID')
    urn = fields.Char('URN')
    amount = fields.Float('AMOUNT')
    instrument_no=fields.Char('INSTRUMENT NUMBER')
    instrument_date =fields.Date('INSTRUMENT DATE')
    pay_mode = fields.Selection([('C','C'),('F','F'),('L','L')], 'Pay Mode')
    transaction_date= fields.Date('TRANSACTION DATE')
    isure_id = fields.Char('ISURE ID')
    micr_code = fields.Char('MICR CODE')
    bank_name= fields.Char('Bank Name')
    branch_name= fields.Char('Branch Name')
    client_code = fields.Char('Client Code')
    user_id = fields.Char('userId')
    paswd = fields.Char('User Password')
    is_excel= fields.Boolean('Is Excel')
    clear_flag= fields.Selection([('cleared', 'Cleared'),('not_cleared', 'Not Cleared')], 'Clear Flag', default='not_cleared')
    
    
    @api.model
    def create(self, vals):
        res = super(bank_challan_transaction, self).create(vals)
        res.process_chellan()
        return res
    
    
    @api.model
    def process_chellan(self):
        for record in self.env['bank.challan.transaction'].sudo().search([('clear_flag','=','not_cleared')]):
            print ("Processing IBankTransaction: %s", record.ibank_transaction_id)
            admission_id = self.env['pappaya.admission'].sudo().search(['|','|',('admission_no','=',record.urn),
                                                                           ('res_no','=',record.urn),
                                                                           ('virtual_acc_no','=',record.urn)], limit=1)
            if admission_id:
                fee_collection_id = self.env['pappaya.fees.collection'].search([('enquiry_id', '=', admission_id.id)])
                Pay_mode_id = self.env['pappaya.paymode'].sudo().search([('is_challan','=',True)])
                fee_collection_id.write({'pay_amount':record.amount, 'payment_mode_id':Pay_mode_id.id,
                                         'bank_chellan_id':record.id,
                                         })
                if fee_collection_id:
                    fee_collection_id.fee_pay()
                    record.clear_flag = 'cleared'
        return True




