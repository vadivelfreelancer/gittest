# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PappayaFeesRefund(models.Model):
    _name = 'pappaya.fees.refund'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Pappaya Fees Refund"
    _order = 'id desc'
    _rec_name = 'student_id'

    @api.one
    @api.constrains('academic_year_id', 'admission_id', 'state')
    def check_state(self):
        if len(self.search([('academic_year_id', '=', self.academic_year_id.id),
                            ('admission_id', '=', self.admission_id.id),
                            ('state', 'in', ['draft', 'requested'])])) > 1:
            raise ValidationError('The Refund request already exists..!')

    def check_refund_amount(self):
        if self.refund_amount <= 0.0:
            raise ValidationError('Refund amount should be greater than Zero..!')
        elif self.refund_amount > self.total_paid:
            raise ValidationError('Refund amount should not be greater than Total paid amount..!')

    def check_deducted_amount(self):
        if self.deducted_amount < 0.0:
            raise ValidationError('Deducted amount should not be less than Zero..!')
        elif self.deducted_amount > self.total_paid:
            raise ValidationError('Deducted amount should not be greater than Total paid amount..!')

    @api.one
    @api.constrains('ifsc_no')
    def check_ifsc_no(self):
        if self.ifsc_no:
            if len(self.ifsc_no) < 11 or not self.ifsc_no.isalnum():
                raise ValidationError('Please enter a valid 11 digit IFSC')

    @api.one
    @api.constrains('account_number', 'father_name')
    def check_account_number(self):
        if self.account_number:
            valid_ac_number = re.match('^[\d]*$', self.account_number)
            if not valid_ac_number:
                raise ValidationError("Please enter valid Account Number.")
        if self.bank_name and len(self.account_number) != self.bank_name.account_number_length:
            raise ValidationError(_("Account Number should be %s digits for %s") % (
                self.bank_name.account_number_length, self.bank_name.name))
        if self.father_name and self.account_number:
            if len(self.search(
                    [('father_name', '!=', self.father_name), ('account_number', '=', self.account_number)])) > 1:
                raise ValidationError('The Account Number already exists..!')

    @api.onchange('refund_amount')
    def onchange_refund_amount(self):
        if self.refund_amount:
            self.check_refund_amount()

    @api.onchange('deducted_amount')
    def onchange_deducted_amount(self):
        if self.deducted_amount:
            self.check_deducted_amount()

    @api.onchange('ifsc_no')
    def onchange_ifsc_no(self):
        self.check_ifsc_no()

    @api.onchange('account_number')
    def onchange_account_no(self):
        self.check_account_number()

    academic_year_id = fields.Many2one('academic.year', 'Academic Year',
                                       default=lambda self: self.env['academic.year'].search(
                                           [('is_active', '=', True)]))
    branch_id = fields.Many2one('operating.unit', string='Branch')
    code = fields.Char(string='Branch Code', related='branch_id.code')
    student_id = fields.Many2one('res.partner', string='Student Name')
    admission_no = fields.Char('Admission No', size=100)
    father_name = fields.Char(string='Father Name', size=150)
    package_id = fields.Many2one('pappaya.course.package', string='Course Package')
    fees_collection_id = fields.Many2one('pappaya.fees.collection', string='Collection')
    state = fields.Selection([('draft', 'Draft'), ('request', 'Requested'), ('confirm', 'Confirmed'),
                              ('approve', 'Approved'), ('freeze', 'Locked'), ('reject', 'Rejected')], 'Status',
                             default='draft', track_visibility='onchange')
    refund_line_ids = fields.One2many('pappaya.fees.refund.line', 'refund_id', string='Refund Line')
    refund_reason = fields.Text('Reason for Refund', size=300)

    bank_name = fields.Many2one('res.bank', 'Bank Name', track_visibility='onchange')
    is_fees_refund = fields.Boolean('Is Fees Refunded?')
    refund_cancel_form = fields.Binary('Refund/Cancel Form')
    file_name = fields.Char('Filename', size=150)

    ifsc_no = fields.Char('IFSC', size=11, track_visibility='onchange')
    account_number = fields.Char('Account Number', size=30, track_visibility='onchange')
    attachment_ids = fields.Many2many('ir.attachment', string='Passbook')

    total_paid = fields.Float('Total Paid', compute='compute_paid_amount', track_visibility='onchange')
    refund_amount = fields.Float('Refund Amount', track_visibility='onchange')
    deducted_amount = fields.Float('Deducted Amount', track_visibility='onchange')
    is_update = fields.Boolean(string='Is Update?', default=False)
    refund_type = fields.Selection(
        [('reservation', 'Reservation'), ('admission', 'Admission'), ('internal_transfer', 'Internal Transfer'),
         ('external_transfer', 'External Transfer'), ('transport', 'Transport'),
         ('other_collection', 'Other Collection'), ('material', 'Material')], default='other_collection',
        string='Refund Type')

    authorize_id = fields.Many2one('pappaya.imulpay.authorize', string='iMulPay Authorize')
    is_authorize = fields.Boolean(string='Is Authorize?', default=False)

    @api.onchange('refund_amount')
    @api.depends('total_paid', 'refund_amount')
    def compute_deducted_amount(self):
        if self.refund_amount:
            self.deducted_amount = self.total_paid - self.refund_amount

    @api.one
    @api.depends('refund_line_ids.is_select')
    def compute_paid_amount(self):
        for rec in self:
            if rec.refund_type == 'other_collection':
                rec.total_paid = sum([i.total_paid + i.res_adj_amt for i in rec.refund_line_ids if i.is_select])
            elif rec.refund_type in ['reservation', 'admission', 'internal_transfer', 'external_transfer']:
                rec.total_paid = sum([i.total_paid for i in rec.refund_line_ids if i.is_select])
            else:
                rec.total_paid = 0.0

    @api.onchange('deducted_amount')
    @api.depends('total_paid', 'deducted_amount')
    def compute_refund_amount(self):
        if self.deducted_amount:
            self.refund_amount = self.total_paid - self.deducted_amount

    @api.onchange('admission_id')
    def onchange_admission(self):
        if self.admission_id:
            student_obj = self.env['res.partner'].search([('admission_id', '=', self.admission_id.id)], limit=1)
            if student_obj:
                self.student_id = student_obj.id
                self.admission_no = student_obj.admission_no
                self.branch_id = student_obj.school_id.id
                self.father_name = student_obj.father_name

    @api.multi
    def get_refund_fees(self):
        if self.admission_id:
            student_obj = self.env['res.partner'].search([('admission_id', '=', self.admission_id.id)])
            fees_collection_obj = self.env['pappaya.fees.collection'].search(
                [('enquiry_id', '=', self.admission_id.id), ('academic_year_id', '=', self.academic_year_id.id)])

            if len(fees_collection_obj.ids) > 1:
                raise ValidationError('More than one Fee Collection is there in same academic year, \n'
                                      'Verify Admission and Fees Collection Records')
            if student_obj:
                ret_fee_heads = []
                if fees_collection_obj:
                    if [s.id for s in fees_collection_obj.fees_collection_line if not s.name.is_soa_fee and
                            not s.is_refunded and s.name.is_refundable_fee and s.term_state == 'processing']:
                        raise ValidationError('The Payment is in Processing..!')

                    self.fees_collection_id = fees_collection_obj.id
                    for i in fees_collection_obj.fees_collection_line:
                        amount = i.total_paid + i.res_adj_amt
                        if not i.name.is_soa_fee and i.name.is_refundable_fee and \
                                not i.is_refunded and amount > 0.0:  # and i.term_state == 'paid'
                            ret_fee_heads.append((0, 0, {'fees_head_id': i.name.id,
                                                         'amount': i.amount,
                                                         'due_amount': i.due_amount,
                                                         'res_adj_amt': i.res_adj_amt,
                                                         'total_paid': i.total_paid,
                                                         'cgst': i.cgst,
                                                         'sgst': i.sgst,
                                                         'term_state': i.term_state,
                                                         'gst_total': i.gst_total}))

                    if len(ret_fee_heads) > 0:
                        self.refund_line_ids = ret_fee_heads
                    else:
                        raise ValidationError('There is no Refundable Fees..!')

                else:
                    raise ValidationError('There is no Fees Collection for this Student..!')
            else:
                raise ValidationError('No Record found for given Admission No.')
            self.is_update = True

    @api.multi
    def refund_approve(self):
        self.state = 'approve'

    @api.multi
    def update_refund(self):
        leger_id = self.env['pappaya.fees.ledger'].search([('fee_collection_id', '=', self.fees_collection_id.id)])
        today = fields.date.today()
        heads = [r.fees_head_id.id for r in self.refund_line_ids if r.is_select]
        for line in self.fees_collection_id.fees_collection_line:
            if line.name.id in heads:
                line.write({'is_refunded': True})
        self.fees_collection_id.write(
            {'is_refunded': True, 'refund_amount': self.fees_collection_id.refund_amount + self.refund_amount})

        leger_id.write({'fee_refund_ledger_line': [(0, 0, {
            'amount': self.refund_amount,
            'posting_date': today,
            'transaction_remarks': self.refund_reason})]})

        if self.refund_type in ['reservation', 'admission']:
            leger_id.write({'fee_cancel_ledger_line': [(0, 0, {
                'amount': self.refund_amount,
                'posting_date': today,
                'remarks': str(self.refund_type.title()) + ' Cancelled - ' + str(self.refund_reason)})]})
        elif self.refund_type in ['internal_transfer', 'external_transfer']:
            leger_id.write({'fee_cancel_ledger_line': [(0, 0, {
                'amount': self.refund_amount,
                'posting_date': today,
                'remarks': str(self.refund_type.title()) + ' - ' + str(self.refund_reason)})]})

        if not self.refund_type in ['internal_transfer', 'external_transfer']:
            self.admission_id.active = False
            self.admission_id.partner_id.active = False
        self.is_authorize = True
        self.state = 'freeze'

    @api.multi
    def refund_request(self):
        self.check_refund_amount()
        self.check_deducted_amount()
        self.state = 'request'

    @api.multi
    def refund_confirm(self):
        self.state = 'confirm'

    @api.multi
    def refund_reject(self):
        self.state = 'reject'


class PappayaFeesReceiptInherit(models.Model):
    _inherit = 'pappaya.fees.receipt'

    refund_id = fields.Many2one('pappaya.fees.refund', 'Refund')


class PappayaFeesRefundLine(models.Model):
    _name = 'pappaya.fees.refund.line'

    is_select = fields.Boolean('Select')
    fees_head_id = fields.Many2one('pappaya.fees.head', 'Fee Type')
    amount = fields.Float('Amount')
    due_amount = fields.Float('Due Amount', )
    res_adj_amt = fields.Float('Reservation Adjustment')
    refund_amount = fields.Float('Refund Amount')
    total_paid = fields.Float('Total Paid')
    cgst = fields.Float('CGST')
    sgst = fields.Float('SGST')
    gst_total = fields.Float('Total')
    term_state = fields.Selection(
        [('due', 'Due'), ('open', 'Open'), ('paid', 'Paid'), ('processing', 'Processing'), ('transfer', 'Transfer')],
        'Status')
    refund_id = fields.Many2one('pappaya.fees.refund', 'Refund')
