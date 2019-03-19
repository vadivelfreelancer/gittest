# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PappayaFeesLedger(models.Model):
    _name = 'pappaya.fees.ledger'
    _rec_name = 'enquiry_id'

    active = fields.Boolean('Active', default=True)
    school_id = fields.Many2one('operating.unit', 'Branch', default=lambda self : self.env.user.company_id)
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    enrollment_number = fields.Char('Enrollment Number',size=100)
    fee_collection_id = fields.Many2one('pappaya.fees.collection', 'Collection ID')
    fee_ledger_line = fields.One2many('pappaya.fees.ledger.line','fees_ledger_id','Ledger')
    fee_receipt_ledger_line = fields.One2many('pappaya.fees.receipt.ledger','fees_ledger_id', 'Ledger Receipt')
    fee_refund_ledger_line = fields.One2many('pappaya.fees.refund.ledger','fees_ledger_id','Fees Refund')
    fee_cancel_ledger_line = fields.One2many('pappaya.fees.cancel.ledger','fees_ledger_id','Fees Cancelled')
    course_id = fields.Many2one('pappaya.course', string='Course')
    group_id = fields.Many2one('pappaya.group', string='Group')
    batch_id = fields.Many2one('pappaya.batch', string='Batch')
    package = fields.Many2one('pappaya.package', string='Package')
    package_id = fields.Many2one('pappaya.course.package', string='Course Package')
    enquiry_id = fields.Many2one('pappaya.admission', 'Admission')
    
    @api.multi
    def get_school(self):
        school_list = []
        if self.school_id:
            vals = {}
            vals['school_id'] = self.school_id.name
            vals['logo'] = self.school_id.logo
            vals['street'] = self.school_id.tem_street if self.school_id.tem_street else ''
            vals['street2'] = self.school_id.tem_street2 if self.school_id.tem_street2 else ''
            vals['city'] = self.school_id.tem_city_id.name if self.school_id.tem_city_id else ''
            vals['zip'] = self.school_id.tem_zip if self.school_id.tem_zip else ''
            vals['phone'] = self.school_id.phone if self.school_id.phone else ''
            vals['fax'] = self.school_id.fax_id if self.school_id.fax_id else ''
            vals['email'] = self.school_id.email if self.school_id.email else ''
            vals['website'] = self.school_id.website if self.school_id.website else ''
            school_list.append(vals)
        return school_list 
    
    @api.multi
    def generate_ledger_report(self):
        return self.env.ref('pappaya_fees.print_student_fee_ledger').get_report_action(self)
    
    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")  
      

class PappayaFeesLedgerLine(models.Model):
    _name = 'pappaya.fees.ledger.line'

    fee_line_id = fields.Many2one('student.fees.collection','Fees Line Head')
    fee_term_state = fields.Selection([('due', 'Due'),('unclear', 'Uncleared'), ('paid', 'Paid'), ('refund', 'Transferred'),('fee_refund','Refund')],related='fee_line_id.term_state', string='Status')
    balance_with_clear = fields.Float(compute='calculate_balance_with_clear',string='Fee Due')
    name = fields.Char(related='fee_line_id.name.name',string='Fee Type')
    credit = fields.Float('Total Fee')
    debit = fields.Float('Fee Deposited')
    balance = fields.Float(string='Fee Due',compute='calculate_balance')
    fees_ledger_id = fields.Many2one('pappaya.fees.ledger','Ledger')
    concession_type_id = fields.Many2one('pappaya.concession.type', 'Concession Type')
    concession_amount = fields.Float('Concession')
    refund_amount = fields.Float('Refund Amount')
    res_adj_amt = fields.Float('Reservation Adjustment')

    @api.one
    @api.depends('balance')
    def calculate_balance(self):
        for s in self.fee_line_id.collection_id.fees_collection_line:
            if s.name.is_reservation_fee and self.fee_line_id.name.is_reservation_fee and s.name.name == self.fee_line_id.name.name:
                self.balance = s.due_amount - s.concession_amount
            elif not self.fee_line_id.name.is_reservation_fee:
                self.balance = self.credit - self.concession_amount - (self.res_adj_amt + self.debit)


    @api.one
    @api.depends('balance_with_clear')
    def calculate_balance_with_clear(self):
        if self.fee_term_state == 'unclear':
            previous_receipt = self.env['pappaya.fees.receipt'].search([('fee_collection_id','=', self.fee_line_id.collection_id.id),('payment_mode_id.is_cash','=', False),('receipt_status', '=','uncleared'),('state','not in',['refund','cancel'])])
            for receipt in previous_receipt:
                for receipt_line in receipt.fees_receipt_line:
                    if self.name == receipt_line.name:
                        self.balance_with_clear = self.balance + receipt_line.amount
        else:
            self.balance_with_clear = self.balance


class PappayaFeesReceiptLedger(models.Model):
    _name = 'pappaya.fees.receipt.ledger'
    
    name = fields.Char('Receipt No',size=100)
    posting_date = fields.Date('Transaction Date')
    fees_head = fields.Char('Fee Type',size=100)
    transaction = fields.Char('Remarks',size=100)
    amount = fields.Float('Amount')
    concession_amount = fields.Float('Concession')
    payment_mode_id = fields.Many2one('pappaya.paymode', 'Payment Mode')
    payment_mode = fields.Selection([('paytm','Paytm'),('payumoney','PayUmoney'),('cash', 'Cash'),('cheque/dd','Cheque'),('dd','DD'), ('neft/rtgs', 'Neft/RTGS'), ('card', 'POS')], string='Payment Mode')
    fees_ledger_id = fields.Many2one('pappaya.fees.ledger','Ledger')
    fees_receipt_id = fields.Many2one('pappaya.fees.receipt','Receipt ID')
    res_adj_amt = fields.Float('Reservation Adjustment')


class pappayaFeesRefundLegder(models.Model):
    _name = 'pappaya.fees.refund.ledger'
       
    fees_head = fields.Many2one('pappaya.fees.head', 'Fee Type')
    amount = fields.Float('Amount')
    posting_date = fields.Date('Refund Date')
    fees_ledger_id = fields.Many2one('pappaya.fees.ledger', 'Ledger')
    fees_receipt_id = fields.Many2one('pappaya.fees.receipt', 'Receipt ID')
    transaction_remarks = fields.Text('Remarks', size=300)
    
    
class pappayaFeesCancelLegder(models.Model):
    _name = 'pappaya.fees.cancel.ledger'
       
    fees_head = fields.Char('Fees Head', size=30)
    remarks = fields.Text('Remarks', size=300)
    amount = fields.Float('Amount')
    posting_date = fields.Date('Cancel Date')
    fees_ledger_id = fields.Many2one('pappaya.fees.ledger', 'Ledger')
    

