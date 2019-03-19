# -*- coding: utf-8 -*-
import logging
import re
from datetime import datetime, date

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PappayaPocketMoney(models.Model):
    _name = 'pappaya.pocket.money'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_id'
    _order = 'id desc'

    pocket_type = fields.Selection([('deposit', 'Deposit'), ('withdraw', 'Withdraw')], default='deposit',
                                   track_visibility="onchange")
    admission_no = fields.Char(string='Admission No')
    student_id = fields.Many2one('res.partner', string='Student', track_visibility="onchange")
    image = fields.Binary(string="Logo", attachment=True, related='student_id.image', store=True)
    academic_year_id = fields.Many2one('academic.year', "Academic Year", related='student_id.joining_academic_year_id',
                                       store=True)
    branch_id = fields.Many2one('operating.unit', string='Branch', related='student_id.school_id', store=True)
    code = fields.Char(string='Branch Code', related='branch_id.code')
    name = fields.Char(string='Student Name', related='student_id.student_full_name', store=True)
    father_name = fields.Char(string='Father Name', related='student_id.father_name', store=True)
    balance_amount = fields.Float(string='Balance Amount', compute='compute_balance_amt', store=True)
    deposit_amount = fields.Float(string='Deposit Amount', track_visibility="onchange")
    withdraw_amount = fields.Float(string='Withdraw Amount', track_visibility="onchange")
    transfer_amount = fields.Float(string='Transfer Amount', track_visibility="onchange")
    date = fields.Date(string='Date', default=lambda self: fields.Date.today())
    paymode_id = fields.Many2one('pappaya.paymode', string='Payment Mode')
    cheque_dd_no = fields.Char(string='Cheque/DD No')
    cheque_dd_date = fields.Char(string='Cheque/DD Date')
    cheque_dd_bank = fields.Many2one('res.bank', string='Cheque/DD Bank')
    cheque_dd_branch = fields.Char(string='Cheque/DD Branch')
    head_id = fields.Many2one('pappaya.fees.head', string='Head Name')
    sub_head_id = fields.Many2one('account.account', string='Sub Fee Type')
    remarks = fields.Text(string='Remarks', track_visibility="onchange")
    payment_mode_id = fields.Many2one('pappaya.paymode', 'Payment Mode')
    transaction_type = fields.Many2one('pappaya.master', 'Transaction Type')
    is_show_card_details = fields.Boolean('Show Card Details')
    is_show_cheque_dd_details = fields.Boolean('Is Show Cheque Details')
    is_show_cash_details = fields.Boolean('Is Show Cash Details')
    is_fee_created = fields.Boolean('Is Fee Created?')
    user_id = fields.Many2one('res.users', string='Current User', default=lambda self: self.env.user,
                              track_visibility="onchange")
    state = fields.Selection(
        [('draft', 'Draft'), ('processing', 'Processing'), ('paid', 'Paid'), ('deposit', 'Deposited'),
         ('transfer', 'Transfered'), ('withdraw', 'Withdrawn')], default='draft', string='State',
        track_visibility="onchange")
    card_holder_name = fields.Char('Card Holder Name')
    card_number = fields.Char('Card Number')
    # card_type = fields.Many2one('pappaya.master', 'Card Type')
    card_type = fields.Char('Card Type')
    bank_machine_id = fields.Many2one('bank.machine', 'Bank Machine')
    bank_machine_type_id = fields.Many2one('pappaya.master', 'Bank Machine Type',
                                           related='bank_machine_id.bank_machine_type_id')
    mid_no = fields.Char('M.I.D.No(last 6 digits)')
    tid_no = fields.Char('T.I.D.No')
    cheque_dd = fields.Char('Cheque/DD No', size=30)
    cheque_date = fields.Date('Cheque Date')
    bank_name = fields.Many2one('res.bank', 'Bank Name')
    is_paid = fields.Boolean('Is Paid?', default=False)
    pos_reference_no = fields.Char('POS Ref No.')
    pos_api_response = fields.Text('POS API Response')

    @api.onchange('cheque_dd')
    def onchange_cheque_dd(self):
        for rec in self:
            if rec.cheque_dd:
                cheque_dd = re.match('^[\d]*$', rec.cheque_dd)
                if not cheque_dd:
                    raise ValidationError(_("Please enter a valid Cheque/DD Number"))

    @api.multi
    def _update_values(self, student_obj):
        for stud in student_obj:
            self.student_id = stud.id

    @api.onchange('admission_no')
    def _onchange_admission_no(self):
        if self.admission_no:
            student_obj = self.env['res.partner'].search(
                [('user_type', '=', 'student'), ('admission_no', '=', self.admission_no), ('active', '=', True)])
            if student_obj:
                self._update_values(student_obj)
            if not student_obj:
                raise ValidationError('Please enter the valid admission number')
            student_cancel_obj = self.env['res.partner'].search(
                [('user_type', '=', 'student'), ('admission_no', '=', self.admission_no),
                 ('admission_id.cancel', '=', True), ('active', '=', True)])
            if student_cancel_obj:
                raise ValidationError('Cancelled Admission Number')
            if self.admission_no and len(self.search([('admission_no', '=', self.admission_no), ('state', 'in', ['draft', 'processing'])])) > 1:
                raise ValidationError('Already record existed for given admission number in Draft or Processing stage')

    @api.one
    def copy(self, default=None):
        raise ValidationError('You are not allowed to Duplicate')

    @api.multi
    def unlink(self):
        raise ValidationError('Sorry,You are not authorized to delete record')

    @api.onchange('payment_mode_id')
    def onchange_payment_mode_id(self):
        self.is_show_card_details = True if self.payment_mode_id.is_card else False
        self.is_show_cheque_dd_details = True if self.payment_mode_id.is_cheque else False
        self.is_show_cash_details = True if self.payment_mode_id.is_cash else False

    @api.depends('student_id')
    def compute_balance_amt(self):
        self.balance_amount = self.student_id.student_wallet_amount

    @api.one
    @api.constrains('deposit_amount', 'transfer_amount', 'withdraw_amount', 'admission_no')
    def check_amount(self):
        if self.deposit_amount and self.deposit_amount <= 0.0:
            raise ValidationError(('Deposit Amount should be greater than zero.'))
        if self.transfer_amount and self.transfer_amount <= 0.0:
            raise ValidationError(('Transfer Amount should be greater than zero.'))
        if self.withdraw_amount and self.withdraw_amount <= 0.0:
            raise ValidationError(('Withdraw Amount should be greater than zero.'))
        if self.admission_no:
            student_obj = self.env['res.partner'].search(
                [('user_type', '=', 'student'), ('admission_no', '=', self.admission_no), ('active', '=', True)])
            if not student_obj:
                raise ValidationError('Please enter the valid admission number')
            student_cancel_obj = self.env['res.partner'].search(
                [('user_type', '=', 'student'), ('admission_no', '=', self.admission_no),
                 ('admission_id.cancel', '=', True), ('active', '=', True)])
            if student_cancel_obj:
                raise ValidationError('Cancelled Admission Number')
            if self.admission_no and len(self.search([('admission_no', '=', self.admission_no), ('state', 'in', ['draft', 'processing'])])) > 1:
                raise ValidationError('Already record existed for given admission number in Draft or Processing stage')

    @api.onchange('pocket_type')
    def onchange_pocket_type(self):
        if self.pocket_type == 'deposit':
            self.head_id, self.sub_head_id = [], []
            self.transfer_amount = 0.0
            self.withdraw_amount = 0.0
        if self.pocket_type == 'withdraw':
            self.head_id, self.sub_head_id = [], []
            self.deposit_amount = 0.0
            self.transfer_amount = 0.0
        if self.pocket_type == 'withdraw':
            return {'domain': {'payment_mode_id': [('is_cash', '=', True)]}}

    @api.onchange('withdraw_amount')
    def onchange_withdraw_amount(self):
        if self.withdraw_amount and self.withdraw_amount > self.balance_amount:
            raise ValidationError('Exceeds the balance amount')

    @api.multi
    def action_send_sms(self):
        mobile = '91' + str(
            self.student_id.father_mobile if self.student_id.father_mobile else self.student_id.mother_mobile).strip()
        message = ''
        substitutions = {'$NAME$': str(self.student_id.student_full_name),
                         '$AMOUNT$': str(self.withdraw_amount),
                         '$DATE$': str(date.today().strftime('%d-%m-%Y')),
                         }
        substrings = sorted(substitutions, key=len, reverse=True)
        regex = re.compile('|'.join(map(re.escape, substrings)))
        sms_content = self.env['pappaya.sms.content'].search(
            [('type', '=', 'money_withdraw'), ('active', '=', True)], limit=1)
        if sms_content:
            message = regex.sub(lambda match: substitutions[match.group(0)], sms_content.description)
        else:
            _logger.info('Unable to send SMS, There is no SMS Content for Pocket Money Withdraw.')
        self.env['pappaya.fees.collection']._send_sms(mobile, message)
        return True

    @api.multi
    def action_transaction(self):
        if self.admission_no:
            student_obj = self.env['res.partner'].search(
                [('user_type', '=', 'student'), ('admission_no', '=', self.admission_no), ('active', '=', True)])
            if not student_obj:
                raise ValidationError('Please enter the valid admission number')
            student_cancel_obj = self.env['res.partner'].search(
                [('user_type', '=', 'student'), ('admission_no', '=', self.admission_no),
                 ('admission_id.cancel', '=', True), ('active', '=', True)])
            if student_cancel_obj:
                raise ValidationError('Cancelled Admission Number')
        head = self.env['pappaya.fees.head'].search([('is_pocket_money', '=', True)])
        if not head:
            raise ValidationError('Please add fee Type for pocket money')

        fees_collection_id = self.env['pappaya.fees.collection'].search(
            [('enquiry_id', '=', self.student_id.admission_id.id),
             ('admission_number', '=', self.student_id.admission_no),
             ('school_id', '=', self.branch_id.id),
             ('academic_year_id', '=', self.student_id.joining_academic_year_id.id)], limit=1)
        if self.pocket_type == 'deposit':
            if fees_collection_id:
                collection_line = self.env['student.fees.collection'].search(
                    [('collection_id', '=', fees_collection_id.id), ('name', '=', head.id)])
                fees_collection_id.write({'pocket_money_id': self.id})
                if collection_line and not self.is_fee_created:
                    collection_line.gst_total += self.deposit_amount;
                    collection_line.amount += self.deposit_amount;
                    collection_line.enquiry_id = self.student_id.admission_id.id
                    collection_line.term_state = 'due';
                    collection_line.pocket_money_id = self.id;
                    collection_line.student_id = self.student_id.id
                    self.is_fee_created = True
                else:
                    if not self.is_fee_created:
                        self.env['student.fees.collection'].create({
                            'collection_id': fees_collection_id.id,
                            'name': head.id,
                            'gst_total': self.deposit_amount,
                            'cgst': 0.0,
                            'sgst': 0.0,
                            'amount': self.deposit_amount,
                            'res_adj_amt': 0.00,
                            'due_amount': self.deposit_amount,
                            'total_paid': 0.0,
                            'term_state': 'due',
                            'enquiry_id': self.student_id.admission_id.id,
                            'pocket_money_id': self.id,
                            'student_id': self.student_id.id,
                        })
                        self.is_fee_created = True
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'pappaya.fees.collection',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'context': {'pocket_money_payment': self.id, 'fee_head_id': head.id},
                    'res_id': fees_collection_id.id,
                    'view_id': self.env.ref('pappaya_fees.pappaya_fees_collection_form', False).id,
                    'target': 'new',
                }

        if self.pocket_type == 'withdraw':
            ledger_obj = self.env['pappaya.fees.ledger'].search([('fee_collection_id', '=', fees_collection_id.id)])
            if ledger_obj:
                self.env['pappaya.fees.refund.ledger'].create({
                    'fees_ledger_id': ledger_obj.id,
                    'fees_head': head.id,
                    'amount': self.withdraw_amount,
                    'posting_date': datetime.today().date(),
                    'transaction_remarks': 'Withdraw : ' + str(self.remarks)
                })
            self.student_id.student_wallet_amount = self.student_id.student_wallet_amount - self.withdraw_amount
            self.write({'state': 'withdraw'})
            self.action_send_sms()
