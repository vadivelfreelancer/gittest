# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm, ValidationError
import re
import time
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class Pappaya_bulk_bank_deposit(models.Model):
    _name = 'pappaya.bulk.bank.deposit'
    _description = "Bulk Bank Deposit"
    _rec_name = 'deposit_slip_no'

    @api.one
    @api.constrains('academic_year_id', 'school_id', 'state')
    def check_state(self):
        if len(self.search([('academic_year_id', '=', self.academic_year_id.id),
                            ('school_id', 'in', self.school_id.ids),
                            ('state', 'in', ['draft', 'requested'])])) > 1:
            raise ValidationError('Cash Deposit already exists..!')

    @api.one
    @api.constrains('collection_date', 'deposit_date')
    def check_deposit_date(self):
        if self.collection_date > self.deposit_date:
            raise ValidationError('Date of Deposit should be greater than Collection Date..!')
        # if self.collection_date and self.collection_date < self.academic_year_id.start_date or self.collection_date > self.academic_year_id.end_date:
        #     raise ValidationError('Collection Date should be within the academic year..!')

    deposit_slip_no = fields.Char('Deposit Slip No.',size=100)
    state = fields.Selection(
        [('draft', 'In hand'), ('requested', 'Requested'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        'Status', default='draft')
    school_id = fields.Many2many('operating.unit', string='Branch')
    deposit_school_id = fields.Many2one('operating.unit', string='Deposit Branch')
    academic_year_id = fields.Many2one('academic.year', string='Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    bank_id = fields.Many2one('res.bank', string='Bank Account Name')
    payment_mode_id = fields.Many2one('pappaya.paymode', 'Payment Mode')
    c_amt_deposit = fields.Float(string='Total Amount Deposited', compute='update_deposit_amt')
    c_bank_id = fields.Many2one('res.bank', string='Deposited Bank')
    c_pay_slip = fields.Binary(string="Deposit Slip")
    file_name = fields.Char('File Name',size=100)
    deposit_date = fields.Date(string='Date of Deposit', default=lambda self: fields.Date.today())
    approve_date = fields.Date(string='Date of Approve')
    collection_date = fields.Date(string='Collection Date')
    bank_deposit_o2m = fields.One2many('bank.deposit','bulk_deposit_id',string='Deposits')
    rec_created = fields.Boolean('Record Created', default=False)

    is_fiscal_year = fields.Boolean(string='Is Fiscal Year?', default=False)
    fiscal_ob = fields.Float(string='Fiscal Opening Balance')
    is_updated = fields.Boolean(string='Update')
    remarks = fields.Text(string='Remarks',size=200)
    total_amt_deposited = fields.Float(string='Total Amount Deposited')
    is_req_bttn = fields.Boolean('Button Hide', default=False)

    @api.onchange('deposit_date')
    def onchange_deposit_date(self):
        if self.deposit_date and self.deposit_date > time.strftime('%Y-%m-%d'):
            raise ValidationError('Date of Deposit should not be in future date!')
        if self.collection_date:
            if self.collection_date > self.deposit_date:
                raise ValidationError('The Date of Deposit should be greater than Collection Date..!')


    @api.onchange('deposit_school_id')
    def onchange_school_id(self):
        # self.c_bank_id = self.collection_date = None
        # self.school_id = None

        # self.cash_receipt_ids = self.c_ref_no = self.c_pay_slip = None
        # self.opening_bal = self.closing_bal = self.c_amt_deposit = self.total_cash_amt = 0.0

        # if self.rec_created == True:
        #     self.write({'closing_bal': 0.0, 'opening_bal': 0.0, 'total_cash_amt': 0.0, 'c_amt_deposit': 0.0})
        if self.deposit_school_id:
            # self.academic_year_id = self.cash_receipt_ids = self.opening_bal = self.closing_bal =
            # self.c_amt_deposit = self.c_ref_no = self.c_pay_slip = None
            domain = []
            if self.deposit_school_id.bank_account_mapping_ids:
                for line in self.deposit_school_id.bank_account_mapping_ids:
                    domain.append(line.bank_id.id)
            return {'domain': {'c_bank_id': [('id', 'in', domain)]}}

    @api.one
    @api.depends('bank_deposit_o2m.c_amt_deposit')
    def update_deposit_amt(self):
        dep_amt = 0.0
        for line in self.bank_deposit_o2m:
            if line.c_amt_deposit > 0:
                dep_amt += line.c_amt_deposit
        self.c_amt_deposit = dep_amt

    @api.multi
    def _attachment_limit_check(self, vals):
        if vals:
            if (len(str(vals)) / 1024 / 1024) > 5:
                raise ValidationError('Attachment size cannot exceed 5MB')

    @api.multi
    def write(self, vals):
        if 'c_pay_slip' in vals.keys() and vals.get('c_pay_slip'):
            self._attachment_limit_check(vals['c_pay_slip'])
        res = super(Pappaya_bulk_bank_deposit, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        if 'c_pay_slip' in vals.keys() and vals.get('c_pay_slip'):
            self._attachment_limit_check(vals['c_pay_slip'])
        vals['rec_created'] = True

        res = super(Pappaya_bulk_bank_deposit, self).create(vals)
        #########
        seq_list = self.search([])
        sequence = len(seq_list.ids)
        res['deposit_slip_no'] = str("{0:08d}".format(0)) + str(sequence + 1)
        ###########
        for dep_line in res.bank_deposit_o2m:
            dep_line.school_id = dep_line.school_id.id
            cash_total = 0.0
            if dep_line.cash_receipt_ids:
                for line in dep_line.cash_receipt_ids:
                    cash_total += line.total
                opening_amount = 0.0
                if dep_line.previous_deposit_id.closing_bal:
                    opening_amount = dep_line.previous_deposit_id.closing_bal
                else:
                    opening_amount = dep_line.opening_bal

                if not (dep_line.fiscal_ob and dep_line.is_fiscal_year):
                    dep_line.opening_bal = opening_amount
                    dep_line.total_cash_amt = cash_total
                    dep_line.grand_total = opening_amount + cash_total
                    dep_line.closing_bal = dep_line.opening_bal + dep_line.total_cash_amt
        return res

    @api.multi
    def action_draft_request(self):
        for res in self.bank_deposit_o2m:
            if res.c_amt_deposit <= 0.0:
                raise ValidationError(_("Please enter Deposit Amount.!"))
            if res.closing_bal < res.c_amt_deposit:
                raise ValidationError(_("Deposit Amount should be less than or equal to Closing Balance"))
        self.write({'state': 'requested'})

    @api.multi
    def action_request_reject(self):
        self.write({'state': 'rejected'})

    @api.multi
    def action_request_approve(self):
        bank_deposit_obj = self.env['bank.deposit']
        for rec in self.bank_deposit_o2m:
            opening_amount = 0.0
            if rec.previous_deposit_id.closing_bal:
                opening_amount = rec.previous_deposit_id.closing_bal
            else:
                opening_amount = rec.opening_bal

            # Account Move
            cash_account = self.env['account.account'].search([('name', '=', 'Cash')])
            bank_account = self.env['account.account'].search([('name', '=', 'Bank')])
            cash_journal_obj = self.env['account.journal'].search([('name', '=', 'Cash')])
            bank_journal_obj = self.env['account.journal'].search([('name', '=', 'Cash')])
            move_lines = []
            move_lines.append((0, 0, {
                'name': 'test11111',  # a label so accountant can understand where this line come from
                'debit': 0,
                'credit': rec.c_amt_deposit,
                'account_id': bank_account.id,  # Course Fee chart of account.
                'date': rec.deposit_date,
                'partner_id': bank_journal_obj.company_id.partner_id.id,
                'journal_id': bank_journal_obj.id,  # Cash journal
                'company_id': bank_journal_obj.company_id.id,
                'currency_id': bank_journal_obj.company_id.currency_id.id,
                'date_maturity': rec.deposit_date
                # or (account.currency_id.id or False),
            }))
            move_lines.append((0, 0, {
                'name': 'test222222',
                'debit': rec.c_amt_deposit,
                'credit': 0,
                'account_id': cash_account.id,  # Reservation Fee head (liability chart of account)
                #                                 'analytic_account_id': context.get('analytic_id', False),
                'date': rec.deposit_date,
                'partner_id': cash_journal_obj.company_id.partner_id.id,
                'journal_id': cash_journal_obj.id,
                'company_id': cash_journal_obj.company_id.id,
                'currency_id': cash_journal_obj.company_id.currency_id.id,  # currency id of narayana
                'date_maturity': rec.deposit_date
                # or (account.currency_id.id or False),
            }))

            # Create account move
            account_move_obj = self.env['account.move'].create({
                #                             'period_id': period_id, #Fiscal period
                'journal_id': bank_journal_obj.id,  # journal ex: sale journal, cash journal, bank journal....
                'date': rec.deposit_date,
                'state': 'draft',
                'company_id': bank_journal_obj.company_id.id,
                'line_ids': move_lines,  # this is one2many field to account.move.line
            })
            # print ('account_move_obj : ', account_move_obj)
            account_move_obj.post()

            rec.sudo().write({'total_amt_deposited': rec.c_amt_deposit,
                              'closing_bal': opening_amount + rec.total_cash_amt - rec.c_amt_deposit,
                              'opening_bal': opening_amount})
            parent_id_exists = True
            next_id = bank_deposit_obj.sudo().search([('previous_deposit_id', '=', rec.id)])
            if next_id:
                for next in next_id:
                    opening_amount = 0.0
                    if next.previous_deposit_id.closing_bal:
                        opening_amount = next.previous_deposit_id.closing_bal
                    else:
                        opening_amount = next.opening_bal
                    if next.state == 'approved':
                        next.sudo().write(
                            {'total_amt_deposited': opening_amount + next.total_cash_amt - next.c_amt_deposit,
                             'opening_bal': opening_amount})
                    else:
                        next.sudo().write({'total_amt_deposited': next.c_amt_deposit,
                                           'closing_bal': opening_amount + next.total_cash_amt,
                                           'opening_bal': opening_amount})
                n_next_id = bank_deposit_obj.sudo().search([('previous_deposit_id', '=', next.id)])
                if not n_next_id:
                    parent_id_exists = False
                while parent_id_exists:
                    for next in n_next_id:
                        if next.previous_deposit_id.closing_bal:
                            opening_amount = next.previous_deposit_id.closing_bal
                        else:
                            opening_amount = next.opening_bal
                        if next.state == 'approved':
                            next.sudo().write({'total_amt_deposited': next.c_amt_deposit,
                                               'closing_bal': opening_amount + next.total_cash_amt - next.c_amt_deposit,
                                               'opening_bal': opening_amount})
                        else:
                            next.sudo().write({'total_amt_deposited': next.c_amt_deposit,
                                               'closing_bal': opening_amount + next.total_cash_amt,
                                               'opening_bal': opening_amount})
                    nn_next_id = bank_deposit_obj.sudo().search([('previous_deposit_id', '=', next.id)])
                    if not nn_next_id:
                        parent_id_exists = False
        self.write({'state': 'approved', 'approve_date': datetime.now().date()})

    """ Button to load payment data"""
    @api.multi
    def get_payment_data(self):
        if self.collection_date and self.collection_date > time.strftime('%Y-%m-%d'):
            raise ValidationError('Collection Date should not be in future date!')

        bank_deposit_obj = self.env['bank.deposit']
        bnk_deposit_id = []
        deposit_list = []
        is_rec_created = False

        self.bank_deposit_o2m.unlink()

        for s in self.school_id:
            exist_cash_list = []
            data_dict = {'opening_bal':0.0}
            for record in bank_deposit_obj.search(
                    [('school_id', '=', s.id), ('academic_year_id', '=', self.academic_year_id.id),
                     ('collection_date', '<=', self.collection_date), ('state', '!=', 'rejected')]):
                for cash in record.cash_receipt_ids:
                    exist_cash_list.append(cash.id)

            ob_ids = bank_deposit_obj.search(
                [('school_id', '=', s.id), ('academic_year_id', '=', self.academic_year_id.id),
                 ('collection_date', '<=', self.collection_date), ('state', '!=', 'rejected'), ], order="id desc", limit=1)
            if ob_ids:
                for ob in ob_ids[0]:
                    data_dict = {
                                  'opening_bal':ob.closing_bal,
                                  # 'previous_deposit_id':ob.id
                                }

            if  self.academic_year_id:
                cash_list = []
                obj = self.env['pappaya.fees.receipt'].sudo().search(
                    [('receipt_date', '<=', self.collection_date), ('school_id', '=', s.id),
                     ('academic_year_id', '=', self.academic_year_id.id), ('id', 'not in', exist_cash_list),
                     ('payment_mode_id.is_cash', '=', True), ('receipt_status', '=', 'cleared'),
                     ('state', 'not in', ['refund', 'cancel'])])
                if obj:
                    receipt_ids = []
                    cash_total = 0.0
                    for receipt in obj:
                        if receipt.total > 0.00:
                            receipt_ids.append(receipt.id)
                            cash_total += receipt.total
                    data_dict['school_id']=s.id
                    data_dict['academic_year_id']=self.academic_year_id.id
                    data_dict['collection_date']=self.collection_date
                    data_dict['cash_receipt_ids'] = [(6, 0, receipt_ids)]
                    data_dict['grand_total'] = data_dict['opening_bal']+ cash_total
                    data_dict['total_cash_amt'] = cash_total
                    data_dict['deposit_date'] = self.deposit_date
                    data_dict['closing_bal'] = (data_dict['opening_bal'] if 'opening_bal' in data_dict else 0.0 ) + cash_total
                    data_dict['bulk_deposit_id'] = self.id
                    data_dict['c_amt_deposit'] = 0.0 #(data_dict['opening_bal'] if 'opening_bal' in data_dict else 0.0 ) + cash_total
                    if data_dict['grand_total'] >0:
                        is_rec_created = True
                        self.env['bank.deposit'].create(data_dict)

        if not is_rec_created:
            raise ValidationError('No Record Found !!!')
        self.is_req_bttn = True


class BankDeposit(models.Model):
    _name = 'bank.deposit'
    _rec_name = 'academic_year_id'

    @api.one
    @api.constrains('c_amt_deposit', 'grand_total')
    def check_deposit_amount(self):
        # if self.c_amt_deposit < 0:
        #     raise ValidationError('Deposite amount should be greater then zero')
        if self.c_amt_deposit > self.grand_total:
            raise ValidationError('Deposit amount should not be greater than Collection amount..!')

    bulk_deposit_id = fields.Many2one('pappaya.bulk.bank.deposit','Bulk Deposit')
    state = fields.Selection([('draft', 'In hand'),('requested', 'Requested'), ('approved', 'Approved'), ('rejected', 'Rejected')], 'Status', default='draft')
    #society_id = fields.Many2one('operating.unit', string='Society',default=_default_society)
    school_id = fields.Many2one('operating.unit', string='Branch')
    academic_year_id = fields.Many2one('academic.year', string='Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    bank_id = fields.Many2one('res.bank', string='Bank Account Name')
    payment_mode_id = fields.Many2one('pappaya.paymode', 'Payment Mode')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    collection_date = fields.Date(string='Collection Date')
    deposit_date = fields.Date(string='Date of Deposit', default=lambda self:fields.Date.today())
    # approve_date = fields.Date(string='Date of Approve')
    # Cash
    cash_receipt_ids = fields.Many2many('pappaya.fees.receipt', 'cash_deposit_fees_receipt_rel','cash_id', 'receipt_id', string='Cash')
    opening_bal = fields.Float(string='Opening Balance')
    closing_bal = fields.Float(string='Closing Balance')
    total_cash_amt = fields.Float(string='Collection Amount')
    c_amt_deposit = fields.Float(string='Amount Deposited')
    # c_bank_id = fields.Many2one('res.bank', string='Deposited Bank')
    c_ref_no = fields.Char(string='Cheque/DD/PoS',size=100)
    #c_pay_slip = fields.Many2many('ir.attachment', string="Pay Slip")
    # c_pay_slip = fields.Binary(string="Deposit Slip")
    # file_name = fields.Char('File Name')

    total_amt_deposited = fields.Float(string='Total Amount Deposited')
    grand_total = fields.Float(string='Grand Total',readonly="1")
    total_cheque_pos_amt = fields.Float(string='Total Amount')
    cleared_amt = fields.Float(string='Cleared Amount')
    uncleared_amt = fields.Float(string='Uncleared Amount')
    remarks = fields.Text(string='Remarks',size=200)
    created_on = fields.Datetime(string='Created On', default=lambda self: fields.Datetime.now())
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    # Fiscal Year
    is_fiscal_year = fields.Boolean(string='Is Fiscal Year?',default=False)
    fiscal_ob = fields.Float(string='Fiscal Opening Balance')
    is_updated = fields.Boolean(string='Update')
    previous_deposit_id = fields.Many2one('bank.deposit')
    rec_created = fields.Boolean('Record Created', default=False)
    deposit_slip_no = fields.Char('Deposit Slip No.',size=100)


    @api.multi
    def update_ob(self):
        if self.is_fiscal_year == True and self.fiscal_ob == 0.0:
            raise ValidationError('Please update the fiscal year opening balance')
        if self.is_fiscal_year == True and self.fiscal_ob > 0.0:
            self.write({'opening_bal':self.fiscal_ob,'is_updated':True})

    @api.onchange('c_amt_deposit')
    def onchange_c_amt_deposit(self):
        if self.c_amt_deposit and self.c_amt_deposit < 0:
            raise ValidationError('Please enter valid Amount..!')

    # @api.onchange('school_id')
    # def onchange_school_id(self):
    #     self.academic_year_id = self.c_bank_id = self.collection_date = None
    #     self.cash_receipt_ids = self.c_ref_no = self.c_pay_slip = None
    #     self.opening_bal = self.closing_bal = self.c_amt_deposit = self.total_cash_amt = 0.0
    #
    #     if self.rec_created == True:
    #         self.write({'closing_bal':0.0, 'opening_bal':0.0, 'total_cash_amt':0.0, 'c_amt_deposit':0.0})
    #     if self.school_id:
    #         # self.academic_year_id = self.cash_receipt_ids = self.opening_bal = self.closing_bal = self.c_amt_deposit = self.c_ref_no = self.c_pay_slip = None
    #         domain = []
    #         if self.school_id.bank_account_mapping_ids:
    #             for line in self.school_id.bank_account_mapping_ids:
    #                 domain.append(line.bank_id.id)
    #         return {'domain': {'c_bank_id': [('id', 'in', domain)]}}


    # @api.onchange('deposit_date')
    # def onchange_deposit_date(self):
    #     if self.deposit_date and self.deposit_date > time.strftime('%Y-%m-%d'):
    #         raise ValidationError('Date of Deposit should not be in future date!')
    #     if self.collection_date:
    #         if self.collection_date > self.deposit_date:
    #             raise ValidationError('The Date of Deposit should be greater than Collection Date..!')

#     @api.onchange('collection_date')
#     def onchange_receipt(self):
#         if self.collection_date and self.collection_date > time.strftime('%Y-%m-%d'):
#             raise ValidationError('Collection Date should not be in future date!')
#         self.cash_receipt_ids = None
#         self.opening_bal = self.closing_bal = self.c_amt_deposit = self.total_cash_amt = 0.0
#         self.c_ref_no = self.c_pay_slip = None
#
#         exist_cash_list = []
#         for record in self.search([('school_id', '=', self.school_id.id),('academic_year_id', '=', self.academic_year_id.id),('collection_date','<=',self.collection_date),('state', '!=','rejected')]):
#             for cash in record.cash_receipt_ids:
#                 exist_cash_list.append(cash.id)
#
#
#         ob_ids = self.search([('school_id','=',self.school_id.id),('academic_year_id','=',self.academic_year_id.id),('collection_date','<=',self.collection_date),('state', '!=','rejected'),],order = "id desc", limit=1)
#         if ob_ids:
#             for ob in ob_ids[0]:
#                 self.opening_bal = ob.closing_bal
#                 self.previous_deposit_id = ob.id
#
# #         fee_obj = self.env['pappaya.fees.receipt'].sudo().search([('receipt_date','=',self.collection_date),('school_id', '=', self.school_id.id),('academic_year_id', '=', self.academic_year_id.id),('id', 'not in', exist_cash_list),('payment_mode','=','cash'),('receipt_status','=','cleared'),('state','not in',['refund','cancel'])])
# #         if self.school_id and self.academic_year_id and not fee_obj and self.opening_bal:
# #             raise ValidationError("Details are unavailable for the selected academic year")
#
#         if self.school_id and self.academic_year_id :
#             cash_list = []
#             obj = self.env['pappaya.fees.receipt'].sudo().search([('receipt_date','<=',self.collection_date),('school_id', '=', self.school_id.id),('academic_year_id', '=', self.academic_year_id.id),('id', 'not in', exist_cash_list),('payment_mode_id.is_cash','=',True),('receipt_status','=','cleared'),('state','not in',['refund','cancel'])])
#             receipt_ids = []
#             for receipt in obj:
#                 if receipt.total > 0.00:
#                     receipt_ids.append(receipt.id)
#             self.cash_receipt_ids = [(6, 0, receipt_ids)]
#             cash_total = 0.0
#             for line in self.cash_receipt_ids:
#                 cash_total += line.total
#             self.grand_total = cash_total
#             self.total_cash_amt = cash_total
#             self.closing_bal = self.opening_bal + self.total_cash_amt

    # @api.multi
    # def _attachment_limit_check(self, vals):
    #     if vals:
    #         if (len(str(vals)) / 1024 /1024) > 5:
    #             raise ValidationError('Attachment size cannot exceed 5MB')
    #
    # @api.multi
    # def write(self, vals):
    #     if 'c_pay_slip' in vals.keys() and vals.get('c_pay_slip'):
    #         self._attachment_limit_check(vals['c_pay_slip'])
    #     res = super(BankDeposit, self).write(vals)
    #     return res
    #
    #
    # @api.model
    # def create(self, vals):
    #     if 'c_pay_slip' in vals.keys() and vals.get('c_pay_slip'):
    #         self._attachment_limit_check(vals['c_pay_slip'])
    #     vals['rec_created'] = True
    #     res = super(BankDeposit, self).create(vals)
    #     cash_total = 0.0
    #     if res.cash_receipt_ids:
    #         for line in res.cash_receipt_ids:
    #             cash_total += line.total
    #     opening_amount = 0.0
    #     if res.previous_deposit_id.closing_bal:
    #         opening_amount = res.previous_deposit_id.closing_bal
    #     else:
    #         opening_amount = res.opening_bal
    #     #########
    #     seq_list =  self.search([])
    #     sequence = len(seq_list.ids)
    #     res['deposit_slip_no'] = str("{0:08d}".format(0)) + str(sequence+1)
    #     ###########
    #     if not (res.fiscal_ob and res.is_fiscal_year):
    #         res['opening_bal'] = opening_amount
    #         res['total_cash_amt'] = cash_total
    #         res['grand_total'] = cash_total
    #         res['closing_bal'] = res['opening_bal'] + res['total_cash_amt']
    #     return res

    # @api.multi
    # def action_draft_request(self):
    #     if self.c_amt_deposit <= 0.0:
    #         raise ValidationError(_("Please enter Deposit Amount.!"))
    #     if self.closing_bal < self.c_amt_deposit:
    #         raise ValidationError(_("Deposit Amount should be less than or equal to Closing Balance"))
    #
    #     for rec in self:
    #         if rec.state != 'approved':
    #             opening_amount = 0.0
    #             cash_total = 0.0
    #             if rec.previous_deposit_id.closing_bal:
    #                 opening_amount = rec.previous_deposit_id.closing_bal
    #             else:
    #                 opening_amount = rec.opening_bal
    #             if not (rec.fiscal_ob and rec.is_fiscal_year):
    #                 #if rec.previous_deposit_id:
    #                 rec.opening_bal = opening_amount
    #             for line in rec.cash_receipt_ids:
    #                     cash_total += line.total
    #             rec.total_cash_amt = cash_total
    #             rec.grand_total = cash_total
    #             rec.total_amt_deposited = rec.c_amt_deposit
    #             rec.closing_bal = rec.opening_bal + rec.total_cash_amt
    #         else:
    #             cash_total = 0.0
    #             for line in rec.cash_receipt_ids:
    #                     cash_total += line.total
    #             rec.grand_total = cash_total
    #             rec.total_amt_deposited = cash_total
    #
    #     self.write({'state': 'requested'})


    # @api.multi
    # def action_request_approve(self):
#         for rec in self:
#             opening_amount = 0.0
#             if rec.previous_deposit_id.closing_bal:
#                 opening_amount = rec.previous_deposit_id.closing_bal
#             else:
#                 opening_amount = rec.opening_bal
#
#             # Account Move
#             cash_account = self.env['account.account'].search([('name','=','Cash')])
#             bank_account = self.env['account.account'].search([('name','=','Bank')])
#             cash_journal_obj = self.env['account.journal'].search([('name','=','Cash')])
#             bank_journal_obj = self.env['account.journal'].search([('name','=','Cash')])
#             move_lines = []
#             move_lines.append((0, 0, {
#                                         'name': 'test11111', # a label so accountant can understand where this line come from
#                                         'debit': 0,
#                                         'credit': rec.c_amt_deposit,
#                                         'account_id': bank_account.id, # Course Fee chart of account.
#                                         'date': rec.deposit_date,
#                                         'partner_id': bank_journal_obj.company_id.partner_id.id,
#                                         'journal_id': bank_journal_obj.id, #  Cash journal
#                                         'company_id': bank_journal_obj.company_id.id,
#                                         'currency_id': bank_journal_obj.company_id.currency_id.id,
#                                         'date_maturity': rec.deposit_date
#                                         #or (account.currency_id.id or False),
#                                     }))
#             move_lines.append((0, 0, {
#                                     'name': 'test222222',
#                                     'debit': rec.c_amt_deposit,
#                                     'credit': 0,
#                                     'account_id': cash_account.id,# Reservation Fee head (liability chart of account)
#     #                                 'analytic_account_id': context.get('analytic_id', False),
#                                     'date': rec.deposit_date,
#                                     'partner_id': cash_journal_obj.company_id.partner_id.id,
#                                     'journal_id': cash_journal_obj.id,
#                                     'company_id': cash_journal_obj.company_id.id,
#                                     'currency_id': cash_journal_obj.company_id.currency_id.id, # currency id of narayana
#                                     'date_maturity': rec.deposit_date
#                                     #or (account.currency_id.id or False),
#                                 }))
#
#             # Create account move
#             account_move_obj = self.env['account.move'].create({
# #                             'period_id': period_id, #Fiscal period
#                             'journal_id': bank_journal_obj.id, # journal ex: sale journal, cash journal, bank journal....
#                             'date': rec.deposit_date,
#                             'state': 'draft',
#                             'company_id': bank_journal_obj.company_id.id,
#                             'line_ids': move_lines, # this is one2many field to account.move.line
#                         })
#             print ('account_move_obj : ', account_move_obj)
#             account_move_obj.post()
#
#             rec.sudo().write({'total_amt_deposited':rec.c_amt_deposit,
#                               'closing_bal':opening_amount + rec.total_cash_amt - rec.c_amt_deposit,
#                               'opening_bal':opening_amount})
#             parent_id_exists = True
#             next_id = self.sudo().search([('previous_deposit_id', '=', rec.id)])
#             if next_id:
#                 for next in next_id:
#                     opening_amount = 0.0
#                     if next.previous_deposit_id.closing_bal:
#                         opening_amount = next.previous_deposit_id.closing_bal
#                     else:
#                         opening_amount = next.opening_bal
#                     if next.state == 'approved':
#                         next.sudo().write({'total_amt_deposited':opening_amount + next.total_cash_amt - next.c_amt_deposit,
#                                            'opening_bal':opening_amount})
#                     else:
#                         next.sudo().write({'total_amt_deposited':next.c_amt_deposit,
#                                            'closing_bal':opening_amount + next.total_cash_amt,
#                                            'opening_bal':opening_amount})
#                 n_next_id = self.sudo().search([('previous_deposit_id', '=', next.id)])
#                 if not n_next_id:
#                     parent_id_exists = False
#                 while parent_id_exists:
#                     for next in n_next_id:
#                         if next.previous_deposit_id.closing_bal:
#                             opening_amount = next.previous_deposit_id.closing_bal
#                         else:
#                             opening_amount = next.opening_bal
#                         if next.state == 'approved':
#                             next.sudo().write({'total_amt_deposited':next.c_amt_deposit,
#                                                'closing_bal':opening_amount + next.total_cash_amt - next.c_amt_deposit,
#                                                'opening_bal':opening_amount})
#                         else:
#                             next.sudo().write({'total_amt_deposited':next.c_amt_deposit,
#                                                'closing_bal':opening_amount + next.total_cash_amt,
#                                                'opening_bal':opening_amount})
#                     nn_next_id = self.sudo().search([('previous_deposit_id', '=', next.id)])
#                     if not nn_next_id:
#                         parent_id_exists = False
#             self.write({'state': 'approved','approve_date':datetime.now().date()})

    # @api.multi
    # def action_request_reject(self):
    #
    #     self.write({'state': 'rejected'})

