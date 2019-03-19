# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class Pappaya_fees_collectioniherit(models.Model):
    _inherit = 'pappaya.fees.collection'
    _rec_name = 'enquiry_id'

    enquiry_id = fields.Many2one('pappaya.admission', "Student Name")
    is_adm_stage = fields.Boolean(string='Is Admission Stage?', related='enquiry_id.is_adm_stage', store=True)
    is_res_stage = fields.Boolean(string='Is Reservation Stage?', related='enquiry_id.is_res_stage', store=True)
    application_no = fields.Char(string='Application No', related='enquiry_id.application_no', store=True)
    admission_number = fields.Char(related='enquiry_id.res_no', string='Admission No', store=True)
    pocket_money_id = fields.Many2one('pappaya.pocket.money', string='Pocket Money')
    course_package_id = fields.Many2one(related='enquiry_id.package_id',comodel_name='pappaya.course.package', string='Course Package')
    medium_id = fields.Many2one(related='enquiry_id.medium_id',comodel_name='pappaya.master', string='Medium')
    residential_type_id = fields.Many2one(related='enquiry_id.residential_type_id',comodel_name='residential.type', string='Student Residential Type')
    adj_amt_total = fields.Float('Total Adjusted Amount', compute='compute_adj_amt_total')
    caution_deposit_amt = fields.Float(string='Caution Deposit', related='enquiry_id.partner_id.caution_deposit')
    student_wallet_amt = fields.Float(string='Pocket Money', related='enquiry_id.partner_id.student_wallet_amount')
    old_new = fields.Selection([('old', 'Old'), ('new', 'New')], string='Old/New Admission', related='enquiry_id.old_new')
    sponsor_amount = fields.Float(string='Sponsor Amount', compute='compute_sponsor_amt')

    @api.depends('enquiry_id', 'enquiry_id.sponsor_amt', 'enquiry_id.sponsor_pay_amt')
    def compute_sponsor_amt(self):
        for rec in self:
            if rec.enquiry_id and rec.enquiry_id.sponsor_type == 'yes' and rec.enquiry_id.sponsor_value == 'partial' and rec.enquiry_id.sponsor_paid == False:
                rec.sponsor_amount = rec.enquiry_id.sponsor_amt + rec.enquiry_id.sponsor_pay_amt
                rec.pay_amount = rec.sponsor_amount

    @api.multi
    @api.depends('fees_collection_line.adjusted_amount')
    def compute_adj_amt_total(self):
        for rec in self:
            rec.adj_amt_total = round(sum(line.adjusted_amount for line in rec.fees_collection_line))

    @api.onchange('pay_amount')
    def onchange_transaction(self):
        d_trans = []
        for rec in self:
            if rec.enquiry_id.stage_id:
                for trans in rec.enquiry_id.stage_id.transaction_type_ids:
                    d_trans.append(trans.id)
                return {'domain': {'transaction_type': [('id', 'in', d_trans)]}}

    @api.multi
    def reservartion_adjustment_receipt_ledger(self ,collect_id, res_head, res_adj_heads):
        receipt_obj = self.env['pappaya.fees.receipt']
        collection_id = collect_id
        reservation_head = res_head
        receipt_ids = self.env['pappaya.fees.receipt'].search([('fee_collection_id' ,'=' ,collection_id.id)])
        partner_obj = None
        if not collection_id.partner_id:
            stu_name = collection_id.enquiry_id.name + '/' + str(collection_id.enquiry_id.id)
            partner_obj = self.env['res.partner'].create({'name': stu_name,
                                                          'company_type': 'person',
                                                          'company_id':self.env.user.company_id.id,
                                                          'school_id': collection_id.school_id.id})
        student_obj  =  partner_obj if partner_obj else collection_id.partner_id
        cash_journal_obj = self.env['account.journal'].search([('code', '=', 'NARFC')])
        for receipt_res in receipt_ids:
            fees_receipt_line_list = []
            move_lines = []

            for receipt_line in receipt_res.fees_receipt_line:
                if receipt_line.name.name == reservation_head.name.name:
                    for collection_line in collection_id.fees_collection_line:
                        if collection_line.res_adj_amt:
                            cgst = 0.00
                            sgst = 0.00
                            without_gst_amt = 0.00
                            cgst_percentage = (100 * collection_line.cgst ) /collection_line.amount
                            sgst_percentage = (100 * collection_line.sgst ) /collection_line.amount
                            cgst = (cgst_percentage * collection_line.total_paid ) /100
                            sgst = (sgst_percentage * collection_line.total_paid ) /100
                            fees_receipt_line_list.append((0, 0, {
                                'name' :collection_line.name.id,
                                'amount' :collection_line.amount,
                                'concession_amount' :collection_line.concession_amount,
                                'concession_type_id' :collection_line.concession_type_id,
                                'total_paid' :collection_line.total_paid,
                                'res_adj_amt' :collection_line.res_adj_amt,
                                'cgst' :cgst,
                                'sgst' :sgst,
                                'without_gst_amt' :without_gst_amt,
                            }))
                            if receipt_res.payment_mode_id.is_cash:
                                move_lines.append((0, 0, {
                                    'name': 'Reservation Fee Adjustment', # a label so accountant can understand where this line come from
                                    'debit': 0,
                                    'credit': collection_line.res_adj_amt,
                                    'account_id': collection_line.name.credit_account_id.id, # Course Fee chart of account.
                                    'date': receipt_res.receipt_date,
                                    'partner_id': student_obj.id,
                                    'journal_id': cash_journal_obj.id,  # Cash journal
                                    'company_id': cash_journal_obj.company_id.id,
                                    'currency_id': cash_journal_obj.company_id.currency_id.id,
                                    'date_maturity': receipt_res.receipt_date,
                                    'operating_unit_id': collection_id.school_id.id,
                                    # or (account.currency_id.id or False),
                                }))
                                move_lines.append((0, 0, {
                                    'name': 'Reservation Fee Adjustment',
                                    'debit': collection_line.res_adj_amt,
                                    'credit': 0,
                                    'account_id': reservation_head.name.credit_account_id.id
                                ,# Reservation Fee head (liability chart of account)
                                    #                                 'analytic_account_id': context.get('analytic_id', False),
                                    'date': receipt_res.receipt_date,
                                    'partner_id': student_obj.id,
                                    'journal_id': cash_journal_obj.id,
                                    'company_id': cash_journal_obj.company_id.id,
                                    'currency_id': cash_journal_obj.company_id.currency_id.id, # currency id of narayana
                                    'date_maturity': receipt_res.receipt_date,
                                    'operating_unit_id': collection_id.school_id.id,
                                    # or (account.currency_id.id or False),
                                }))

                    receipt_status = None
                    if receipt_res.payment_mode_id.is_cash:
                        # Create account move
                        account_move_obj = self.env['account.move'].create({
                            #                             'period_id': period_id, #Fiscal period
                            'journal_id': cash_journal_obj.id, # journal ex: sale journal, cash journal, bank journal....
                            'date': receipt_res.receipt_date,
                            'state': 'draft',
                            'company_id': cash_journal_obj.company_id.id,
                            'line_ids': move_lines, # this is one2many field to account.move.line
                            'operating_unit_id': collection_id.school_id.id,
                        })
                        #                         print 'account_move_obj : ', account_move_obj
                        account_move_obj.post()

                        receipt_status = 'cleared'
                    else:
                        receipt_status = 'uncleared'
                    receipt = receipt_obj.sudo().create({
                        'state' :'paid',
                        'fee_collection_id' :collection_id.id,
                        'school_id' : receipt_res.school_id.id,
                        'academic_year_id' : receipt_res.academic_year_id.id,
                        'name' :receipt_res.name.id,
                        'payment_mode_id': receipt_res.payment_mode_id.id,
                        'cheque_dd' : receipt_res.cheque_dd,
                        'bank_name' :receipt_res.bank_name.id,
                        'remarks' :receipt_res.remarks,
                        'receipt_date' :receipt_res.receipt_date,
                        'fees_receipt_line' :fees_receipt_line_list,
                        'receipt_status' :receipt_status
                    })


                    ledger_obj = self.env['pappaya.fees.ledger']
                    led_obj_ref = ledger_obj.search([('fee_collection_id', '=', collection_id.id)])

                    if receipt.payment_mode_id.is_cash:

                        fee_ledger_line = []
                        fee_receipt_ledger_line = []
                        for rec1 in collection_id.fees_collection_line:
                            fee_ledger_line.append((0, 0, {
                                'fee_line_id' :rec1.id,
                                'name' :rec1.name.name,
                                'credit' :rec1.amount,
                                'concession_amount' :rec1.concession_amount,
                                'concession_type_id' :rec1.concession_type_id.id,
                                'debit' :rec1.total_paid,
                                'res_adj_amt' :rec1.res_adj_amt,
                                'balance' :rec1.amount - rec1.res_adj_amt - (rec1.total_paid + rec1.concession_amount),
                            }))


                        for frl in receipt.fees_receipt_line:
                            fee_receipt_ledger_line.append((0, 0, {
                                'fees_receipt_id': receipt.id,
                                'name' :receipt.id,
                                'posting_date' :receipt.receipt_date,
                                'fees_head' :frl.name.name,
                                'transaction' :receipt.remarks,
                                'concession_amount' :frl.concession_amount,
                                'payment_mode_id' :receipt.payment_mode_id.id,
                                'amount' :frl.total_paid,
                                'res_adj_amt' :frl.res_adj_amt,
                            }))

                        if not led_obj_ref:
                            ledger = ledger_obj.sudo().create({
                                'fee_collection_id' :collection_id.id,
                                'school_id' : collection_id.school_id.id,
                                'academic_year_id' : collection_id.academic_year_id.id,
                                'enquiry_no' : collection_id.enquiry_id.id,
                                'course_id': collection_id.enquiry_id.course_id.id,
                                'group_id': collection_id.enquiry_id.group_id.id,
                                'batch_id': collection_id.enquiry_id.batch_id.id,
                                'package': collection_id.enquiry_id.package.id,
                                'package_id': collection_id.enquiry_id.package_id.id,
                                'fee_ledger_line' :fee_ledger_line,
                                'fee_receipt_ledger_line' :fee_receipt_ledger_line,
                            })
                        else:
                            led_obj_ref.fee_receipt_ledger_line = fee_receipt_ledger_line
                            for receipt_line in receipt.fees_receipt_line:

                                for line in led_obj_ref.fee_ledger_line:

                                    if receipt_line.name.name == line.name :
                                        line.debit += receipt_line.total_paid
                                        line.balance = line.balance - receipt_line.total_paid - receipt_line.res_adj_amt
                    else:
                        if not led_obj_ref:
                            fee_ledger_line = []
                            fee_receipt_ledger_line = []
                            for rec1 in collect_id.fees_collection_line:
                                fee_ledger_line.append((0, 0, {
                                    'fee_line_id' :rec1.id,
                                    'name' :rec1.name.name,
                                    'credit' :rec1.amount,
                                    'concession_amount' :rec1.concession_amount,
                                    'concession_type_id' :rec1.concession_type_id.id,
                                    'debit' :0.00,
                                    'balance' :rec1.amount,
                                    'res_adj_amt' :rec1.res_adj_amt,
                                }))

                            for frl in receipt.fees_receipt_line:
                                fee_receipt_ledger_line.append((0, 0, {
                                    'fees_receipt_id': receipt.id,
                                    'name' :receipt.id,
                                    'posting_date' :receipt.receipt_date,
                                    'fees_head' :frl.name.name,
                                    'transaction' :receipt.remarks,
                                    'concession_amount' :frl.concession_amount,
                                    'payment_mode_id' :receipt.payment_mode_id.id,
                                    'amount' :frl.total_paid,
                                    'res_adj_amt' :frl.res_adj_amt,
                                }))



                            if not led_obj_ref:
                                ledger = ledger_obj.sudo().create({
                                    'fee_collection_id' :record.id,
                                    'school_id' : record.school_id.id,
                                    'academic_year_id' : record.academic_year_id.id,
                                    'enquiry_no' : record.enquiry_id.id,
                                    'course_id': record.enquiry_id.course_id.id,
                                    'group_id': record.enquiry_id.group_id.id,
                                    'batch_id': record.enquiry_id.batch_id.id,
                                    'package': record.enquiry_id.package.id,
                                    'package_id': record.enquiry_id.package_id.id,
                                    'fee_ledger_line' :fee_ledger_line,
                                    'fee_receipt_ledger_line' :fee_receipt_ledger_line
                                })
                        else:
                            fee_receipt_ledger_line = []
                            for frl in receipt.fees_receipt_line:
                                fee_receipt_ledger_line.append((0, 0, {
                                    'fees_receipt_id': receipt.id,
                                    'name' :receipt.id,
                                    'posting_date' :receipt.receipt_date,
                                    'fees_head' :frl.name.name,
                                    'transaction' :receipt.remarks,
                                    'concession_amount' :frl.concession_amount,
                                    'payment_mode_id' :receipt.payment_mode_id.id,
                                    'amount' :frl.total_paid,
                                    'res_adj_amt' :frl.res_adj_amt,
                                }))
                            led_obj_ref.fee_receipt_ledger_line = fee_receipt_ledger_line
        return True

class StudentFeesCollectionLineinherit(models.Model):
    _inherit = 'student.fees.collection'

    enquiry_id = fields.Many2one('pappaya.admission', "Student Name")
    student_id = fields.Many2one('res.partner', string="Student", domain=[('user_type', '=', 'student')])
    admission_number = fields.Char(related='enquiry_id.res_no', string='Admission No', store=True)
    pocket_money_id = fields.Many2one('pappaya.pocket.money', string='Pocket Money')

class PappayaFeesReceiptinherit(models.Model):
    _inherit = 'pappaya.fees.receipt'
    _rec_name = 'name'

    name = fields.Many2one(related='fee_collection_id.enquiry_id', string='Student Name')
    admission_number = fields.Char(related='name.res_no' ,string='Admission No', store=True)
    is_adm_stage = fields.Boolean(string='Is Admission Stage?', related='name.is_adm_stage', store=True)
    is_res_stage = fields.Boolean(string='Is Reservation Stage?', related='name.is_res_stage', store=True)
    application_no = fields.Char(string='Application No', related='name.application_no', store=True)


class PappayaFeesReceiptLine(models.Model):
    _inherit = 'pappaya.fees.receipt.line'

    pocket_money_id = fields.Many2one('pappaya.pocket.money', string='Pocket Money')


class PappayaFeesLedger(models.Model):
    _inherit = 'pappaya.fees.ledger'

    enquiry_id = fields.Many2one('pappaya.admission', 'Student Name')
    admission_number = fields.Char(related='enquiry_id.res_no', string='Admission No', store=True)


class PappayaConcessionFees(models.Model):
    _inherit = 'pappaya.concession.fees'
    _rec_name = 'admission_id'

    admission_id = fields.Many2one('pappaya.admission', string='Admission Number',track_visibility="onchange")
    course_id = fields.Many2one('pappaya.course', string='Course', related='admission_id.course_id', store=True)
    group_id = fields.Many2one('pappaya.group', string='Group', related='admission_id.group_id', store=True)
    batch_id = fields.Many2one('pappaya.batch', string='Batch', related='admission_id.batch_id', store=True)
    package_id = fields.Many2one('pappaya.package', string='Package', related='admission_id.package', store=True)
    course_package_id = fields.Many2one('pappaya.course.package', string='Course Package', related='admission_id.package_id', store=True)


class PappayaFeesRefund(models.Model):
    _inherit = 'pappaya.fees.refund'

    admission_id = fields.Many2one('pappaya.admission', 'Admission No.')
    course_package_id = fields.Many2one('pappaya.course.package', string='Course Package',
                                        related='admission_id.package_id', store=True)
