# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm, ValidationError, UserError
import re
import time
from datetime import datetime, date

class bank_deposit_clearance(models.Model):
    _name = 'bank.deposit.clearance'
    _rec_name = 'payment_mode_id'

#     @api.model
#     def _default_society(self):
#         user_id = self.env['res.users'].sudo().browse(self.env.uid)
#         if len(user_id.company_id.parent_id) > 0 and user_id.company_id.parent_id.type == 'society':
#             return user_id.company_id.parent_id.id
#         elif user_id.company_id.type == 'society':
#             return user_id.company_id.id
# 
#     @api.model
#     def _default_school(self):
#         user_id = self.env['res.users'].sudo().browse(self.env.uid)
#         if user_id.company_id and user_id.company_id.type == 'school':
#             return user_id.company_id.id

    #society_id = fields.Many2one('operating.unit', string='Society', default=_default_society)
    school_id = fields.Many2one('operating.unit', string='Branch')
    academic_year_id = fields.Many2one('academic.year',string='Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    payment_mode_id = fields.Many2one('pappaya.paymode','Payment Mode')
    status = fields.Selection([('draft', 'In hand'),('deposit','Deposited')], string='Status', default='draft')
    payment_line_status = fields.Selection([('uncleared','Uncleared'),('cleared','Done')], string='Status', default='uncleared')
    line_ids = fields.One2many('bank.deposit.clearance.line','bank_clearance_id',string='Bank Deposit Clearance Line')
    status_line_ids = fields.One2many('payment.status.line','bank_clearance_id',string='Payment Status Line')
    total_amt = fields.Float(compute='compute_total_amt', string="Total")
    read_only = fields.Boolean(string="Read Only?")
    cleared_amt = fields.Float(compute='compute_total_amt', string="Cleared Amount")
    c_bank_id = fields.Many2one('res.bank', string='Deposited Bank')
    deposit_bank_id = fields.Many2one('branch.bank.account.mapping', string='Deposited Bank')
    uncleared_amt = fields.Float(compute='compute_total_amt', string="Uncleared Amount")
    rejected_amt = fields.Float(compute='compute_total_amt', string="Rejected Amount")
    created_on = fields.Datetime(string='Date', default=lambda self: fields.Datetime.now())
    confirm_on = fields.Date(string='Date')
    cleared_date = fields.Date(string='Date of Cleared')
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    remarks = fields.Text(string='Remarks',size=300)
    
          
    
#     @api.onchange('society_id')
#     def onchange_society_id(self):
#         if self.society_id:
#             self.academic_year_id = None
#             self.payment_mode_id = None
#             self.line_ids = None
#     
#     @api.constrains('line_ids')
#     def check_line_ids(self):
#         is_select = [ref for ref in self.line_ids.mapped('is_select') if ref]
#         if not is_select:
#             raise ValidationError(_("Please select the record"))

    @api.onchange('school_id')
    def onchange_school_id(self):
        if self.school_id:
            domain = []
            if self.school_id.bank_account_mapping_ids:
                # for line in self.school_id.bank_account_mapping_ids:
                #     domain.append(line.bank_id.id)
                return {'domain': {'deposit_bank_id': [('id', 'in', self.school_id.bank_account_mapping_ids.ids)]}}
        
                    
    @api.multi
    def confirm(self):
        is_select = [ref for ref in self.line_ids.mapped('is_select') if ref]
        if not is_select:
            raise ValidationError(_("Please select the record"))
        line_list = []
        for line in self.line_ids:
            cheque_date = today = delta = False
            if line.cheque_date:
                today = date.today()
                cheque_date = datetime.strptime(line.cheque_date, "%Y-%m-%d").date()
                delta = today - cheque_date
            if line.is_select:
                if line.payment_mode_id.is_cheque and today < cheque_date:
                    raise ValidationError(_("You are Depositing Posted Date cheque (%s -- %s) \n "
                                            "Please unselect..!") %(line.cheque_dd, line.cheque_date))

                if delta and line.payment_mode_id.is_cheque and line.cheque_mode and not line.late_reason and delta.days > 3:
                    raise ValidationError(_("Please enter the Late Reason for this cheque (Ref No:%s)") % line.cheque_dd)
                line_list.append((0,0,{
                                    'receipt_id':line.receipt_id.id, 
                                    'is_select':False,
                                    'receipt_date':line.receipt_date, 
                                    'payment_mode_id': line.payment_mode_id.id,
                                    'cheque_dd': line.cheque_dd or line.receipt_id.tid_no,
                                    'cheque_date': line.cheque_date,
                                    'reason': line.late_reason,
                                    'total':line.total,
                                    'state':'uncleared',
                                    'status':'uncleared',
                                    'attachment':line.attachment,
                                    'file_name':line.file_name
                                }))
                line.write({'state':'deposit','read_only':True})
                
            else:
                line.sudo().unlink()
        if line_list:
            self.status_line_ids = line_list
        self.write({'payment_line_status':'uncleared','status':'deposit','read_only':True,'confirm_on':datetime.now().date()})
    
    @api.multi
    def confirm_cleared(self, parent_id):
        journal_obj = self.env['account.journal'].sudo().search([('code','=','NARFC')], limit=1)
        for line in parent_id.status_line_ids:
            collection_id = line.receipt_id.fee_collection_id
            if line.is_select and line.state == 'uncleared':
                if collection_id.partner_id:
                    partner_id = collection_id.partner_id
                elif collection_id.enquiry_id.partner_id:
                    partner_id = collection_id.partner_id; collection_id.partner_id = collection_id.enquiry_id.partner_id
                else:
                    stu_name = collection_id.enquiry_id.name + '/' + str(collection_id.enquiry_id.id)
                    partner_obj = self.env['res.partner'].create({'name': stu_name, 'company_type': 'person', 'company_id': self.env.user.company_id.id, 'school_id':collection_id.school_id.id})
                    collection_id.partner_id = partner_obj.id; collection_id.enquiry_id.partner_id = partner_obj.id
                if collection_id.enquiry_id.stage_id.sequence > 2 and collection_id.enquiry_id.old_new == 'new':
                    collection_id.enquiry_id.existing_old_student()
                    collection_id.enquiry_id.is_student_created = True
                # LEDGER UPDATE
                ledger_obj = self.env['pappaya.fees.ledger']
                led_obj_ref = ledger_obj.search([('fee_collection_id', '=', line.receipt_id.fee_collection_id.id)])
                for fee_receipt_line in line.receipt_id.fees_receipt_line:
                    for line_ledger in led_obj_ref.fee_ledger_line:
                        if fee_receipt_line.name.name == line_ledger.name :
                            line_ledger.debit += fee_receipt_line.total_paid
                            line_ledger.balance -= fee_receipt_line.total_paid
                                    
                    # OTHER PAYMENT AND POCKET MONEY CLEARANCE
                    if fee_receipt_line.other_payment_id and fee_receipt_line.other_payment_id.id == fee_receipt_line.fees_coll_line_id.other_payment_id.id:
                        fee_receipt_line.other_payment_id.write({'state':'paid'})
                    elif fee_receipt_line.pocket_money_id and fee_receipt_line.pocket_money_id.id == fee_receipt_line.fees_coll_line_id.pocket_money_id.id:
                        fee_receipt_line.pocket_money_id.write({'state':'deposit'})
                        collection_id.partner_id.write({'student_wallet_amount': (collection_id.partner_id.student_wallet_amount + fee_receipt_line.amount)})
                        
                    fees_coll_line_id = fee_receipt_line.fees_coll_line_id
                    if fees_coll_line_id:
                        # ACCOUNTING ENTRIES
                        receipt_amount = fee_receipt_line.total_paid
                        # line_ids = collection_id._get_move_lines(collection_id.partner_id, fees_coll_line_id.name,
                        # receipt_amount, journal_obj, collection_id.school_id)
                        # account_move = collection_id._create_move_entry(journal_obj, collection_id.school_id,
                        # line_ids)
                        # account_move.post()


                        if not self.env['pappaya.fees.receipt.line'].sudo().search([('fees_coll_line_id','=',fees_coll_line_id.id), ('receipt_id.receipt_status','=','uncleared'), ('id','!=',fee_receipt_line.id)]):
                            fees_coll_line_id.term_state = 'paid' if fees_coll_line_id.due_amount == 0.0 else 'due'
                            for_branch = collection_id.enquiry_id.branch_id
                            at_branch = collection_id.enquiry_id.branch_id_at
                            if for_branch == at_branch:
                                collection_id._create_acc_journal_entries(collection_id.partner_id,
                                                                          fees_coll_line_id.name,
                                                                          receipt_amount, journal_obj, collection_id,
                                                                          self.deposit_bank_id)
                            else:
                                self.create_six_acc_journal_ent(collection_id.partner_id,
                                                                fees_coll_line_id.name,
                                                                receipt_amount, journal_obj, collection_id,
                                                                self.deposit_bank_id,
                                                                at_branch, for_branch)

                            # Reservation Adjustment
                            if fees_coll_line_id.name.is_reservation_fee:
                                mandatory_fees, minimum_admission_fee = collection_id.enquiry_id._get_minimum_admisison_mandatory_fees()
                                total_fees_required = mandatory_fees + minimum_admission_fee
                                total_reservatoin_paid = fees_coll_line_id.total_paid
                                if total_reservatoin_paid >= total_fees_required:
                                    collection_id.enquiry_id.adjust_reservation_fees()
                                    collection_id._update_course_fee_paid_status()
                            elif fees_coll_line_id.name.is_course_fee_component:
                                collection_id._update_course_fee_paid_status()
                        else:
                            fees_coll_line_id.write({'term_state':'processing'})
                    
                    # CAUTION DEPOSIT and Pocket Money
                    if fee_receipt_line.name.is_caution_deposit_fee:
                        collection_id.partner_id.caution_deposit += receipt_amount
                    # if fee_receipt_line.name.is_pocket_money:
                    #     partner_id.student_wallet_amount += receipt_amount
                        
                course_fee_ledger_line = self.env['pappaya.fees.ledger.line'].sudo().search([('fees_ledger_id','=',led_obj_ref.id),
                                                                                            ('fee_line_id.name.is_course_fee','=',True)])
                if course_fee_ledger_line:
                    course_fee_ledger_line.write({'debit':0.0,'balance':0.0})
                    for ledger_line in led_obj_ref.fee_ledger_line:
                        if ledger_line.fee_line_id.name.is_course_fee_component and not ledger_line.fee_line_id.name.is_course_fee:
                            course_fee_ledger_line.debit += ledger_line.debit
                            course_fee_ledger_line.balance += ledger_line.balance
                            
                    if (course_fee_ledger_line.debit+course_fee_ledger_line.res_adj_amt) == course_fee_ledger_line.credit:
                        course_fee_ledger_line.fee_term_state = 'paid'
                                    
                line.receipt_id.write({'receipt_status':'cleared'})        
                line.write({'state':'cleared', 'read_only':True})                                    
                            
    @api.multi
    def confirm_rejected(self, parent_id):
        all_receipt_uncleared = False
        for line in parent_id.status_line_ids:
            if line.is_select and line.state == 'uncleared':
                for fee_receipt_line in line.receipt_id.fees_receipt_line:
                    fees_coll_line_id = fee_receipt_line.fees_coll_line_id
                    collection_id = fees_coll_line_id.collection_id
                    # OTHER PAYMENT AND POCKET MONEY CLEARANCE
                    if fee_receipt_line.other_payment_id and fee_receipt_line.other_payment_id.id == fee_receipt_line.fees_coll_line_id.other_payment_id.id: 
                        fee_receipt_line.other_payment_id.write({'state':'draft'})
                    elif fee_receipt_line.pocket_money_id and fee_receipt_line.pocket_money_id.id == fee_receipt_line.fees_coll_line_id.pocket_money_id.id:
                        fee_receipt_line.pocket_money_id.write({'state':'draft'})
                    
                    fees_coll_line_id.write({'total_paid':(fees_coll_line_id.total_paid - fee_receipt_line.total_paid)})    
                    # Reservation Adjustment
                    if fees_coll_line_id.name.is_reservation_fee:
                        mandatory_fees, minimum_admission_fee = collection_id.enquiry_id._get_minimum_admisison_mandatory_fees()
                        total_fees_required = mandatory_fees + minimum_admission_fee
                        total_reservatoin_paid = fees_coll_line_id.total_paid
                        if total_reservatoin_paid >= total_fees_required:
                            if not self.env['pappaya.fees.receipt.line'].sudo().search([('fees_coll_line_id','=',fees_coll_line_id.id), ('receipt_id.receipt_status','=','uncleared'), ('id','!=',fee_receipt_line.id)]):
                                collection_id.enquiry_id.adjust_reservation_fees()
                            
                    if fees_coll_line_id.amount <= fees_coll_line_id.total_paid:
                        if not self.env['pappaya.fees.receipt.line'].sudo().search([('fees_coll_line_id','=',fees_coll_line_id.id), ('receipt_id.receipt_status','=','uncleared'), ('id','!=',fee_receipt_line.id)]):
                            fees_coll_line_id.write({'term_state':'paid'})
                    else:
                        fees_coll_line_id.write({'term_state':'due'})
                    collection_id._update_course_fee_paid_status()
                                             
                line.receipt_id.write({'state':'cancel','receipt_status':'cleared'})
                line.write({'state':'rejected','read_only':True})
                all_receipt_uncleared = False
            else:
                all_receipt_uncleared = True
        if not all_receipt_uncleared:
            parent_id.write({'payment_line_status':'cleared','cleared_date':datetime.now().date()})
    
    @api.onchange('payment_mode_id')
    def onchange_payment_mode(self):
        exist_list = []
        reject_list = []
        self.line_ids = None
        for record in self.search([('school_id', '=', self.school_id.id),('academic_year_id', '=', self.academic_year_id.id),('payment_mode_id','=', self.payment_mode_id.id),('status','=', 'deposit')]):
            for line in record.line_ids:
                if line.is_select: 
                    exist_list.append(line.receipt_id.id)
        for record in self.search([('school_id', '=', self.school_id.id),('academic_year_id', '=', self.academic_year_id.id),('payment_mode_id','=', self.payment_mode_id.id),('status','=', 'deposit')]):
            for line in record.status_line_ids:
                if line.is_select and line.state == 'rejected' and line.receipt_id.receipt_status == 'uncleared':
                    reject_list.append(line.receipt_id.id)
        for reject in reject_list:
            exist_list.remove(reject)
            
        fee_obj = self.env['pappaya.fees.receipt'].sudo().search([('school_id', '=', self.school_id.id),('academic_year_id', '=', self.academic_year_id.id),('id', 'not in', exist_list),('payment_mode_id','=', self.payment_mode_id.id),('receipt_status', '=', 'uncleared'),('state','not in',['refund','cancel'])])
        if self.school_id and self.academic_year_id and not fee_obj:
            raise ValidationError("Details are unavailable for the selected academic year")
        
        if self.school_id and self.academic_year_id :
            cash_list = []
            receipt_obj = self.env['pappaya.fees.receipt'].sudo().search([('school_id', '=', self.school_id.id),('academic_year_id', '=', self.academic_year_id.id),('id', 'not in', exist_list),('payment_mode_id','=', self.payment_mode_id.id),('receipt_status', '=', 'uncleared'),('state','not in',['refund','cancel'])])
            receipt_list = []
            for receipt_line in receipt_obj:
                if receipt_line.total > 0.00:
                    receipt_list.append((0,0,{
                                            'receipt_id':receipt_line.id, 
                                            'is_select':False,
                                            'receipt_date':receipt_line.receipt_date, 
                                            'payment_mode_id': receipt_line.payment_mode_id.id,
                                            'cheque_dd': receipt_line.cheque_dd or receipt_line.tid_no,
                                            'cheque_date': receipt_line.cheque_date,
                                            'cheque_mode': True if receipt_line.payment_mode_id.is_cheque else False,
                                            'total':receipt_line.total,
                                            'receipt_status': receipt_line.receipt_status,
                                            'state':'draft'
                                        }))
            self.line_ids = receipt_list    
    
    @api.one
    @api.depends('status_line_ids')
    def compute_total_amt(self):
        cleared_total,uncleared_total,rejected_total,total = 0.0,0.0,0.0,0.0
        all_receipt_uncleared = False
        if self.status_line_ids:
            for rec in self.status_line_ids:
                if rec.state =='uncleared':
                    uncleared_total+= rec.total
                    all_receipt_uncleared = True
                if rec.state =='cleared':
                    cleared_total+= rec.total
                if rec.state == 'rejected':
                    rejected_total += rec.total
                total+=rec.total
        if not all_receipt_uncleared:
            self.write({'payment_line_status':'cleared','cleared_date':datetime.now().date()})
        self.cleared_amt = cleared_total
        self.uncleared_amt = uncleared_total
        self.rejected_amt = rejected_total
        self.total_amt = total

    @api.multi
    def create_six_acc_journal_ent(self, student_obj, fee_head_obj, amount_paid, journal_obj, collection_id,
                                   deposit_bank, at_branch, for_branch):
        move_lines1 = []
        operating_unit_obj = collection_id.school_id
        if not at_branch.credit_account_id or not at_branch.parent_id.co_debit_account_id:
            raise ValidationError('Please configure Dr/Cr account in Branch/Entity')
        ## Entry 1: At Branch entry #####
        move_lines1.append((0, 0, {
            'name':at_branch.credit_account_id.name,
            'debit': 0,
            'credit': amount_paid,
            'account_id': at_branch.credit_account_id.id,  # Course Fee chart of account.
            'date': str(datetime.today().date()),
            'partner_id': student_obj.id,
            'journal_id': journal_obj.id,  # Cash journal
            'company_id': journal_obj.company_id.id,
            'currency_id': journal_obj.company_id.currency_id.id,
            'date_maturity': str(datetime.today().date()),
            'operating_unit_id': at_branch.id,
            'fees_collection_id': collection_id.id,
        }))

        move_lines1.append((0, 0, {
            'name': at_branch.parent_id.co_debit_account_id.name,
            'debit': amount_paid,
            'credit': 0,
            # 'account_id': student_obj.property_account_receivable_id.id,# Student account
            # ~ 'account_id': fee_head_obj.contra_account_id.id,# Contra Ledger
            'account_id': at_branch.parent_id.co_debit_account_id.id,  # Contra Ledger
            'date': str(datetime.today().date()),
            'partner_id': student_obj.id,
            'journal_id': journal_obj.id,
            'company_id': journal_obj.company_id.id,
            'currency_id': journal_obj.company_id.currency_id.id,  # currency id of narayana
            'date_maturity': str(datetime.today().date()),
            'operating_unit_id': at_branch.parent_id.id,
            'fees_collection_id': collection_id.id,
        }))

        account_move_obj1 = self.env['account.move'].create({
            'journal_id': journal_obj.id,  # journal ex: sale journal, cash journal, bank journal....
            'date': str(datetime.today().date()),
            'state': 'draft',
            'company_id': journal_obj.company_id.id,
            'operating_unit_id': at_branch.id,
            'line_ids': move_lines1,  # this is one2many field to account.move.line
            'fees_collection_id': collection_id.id,
        })
        account_move_obj1.post()

        #### Entry-2: For Branch Entries ####
        move_lines2 = []

        move_lines2.append((0, 0, {
            'name': fee_head_obj.name,
            # a label so accountant can understand where this line come from
            'debit': 0,
            'credit': amount_paid,
            'account_id': fee_head_obj.credit_account_id.id,  # Course Fee chart of account.
            'date': str(datetime.today().date()),
            'partner_id': student_obj.id,
            'journal_id': journal_obj.id,  # Cash journal
            'company_id': journal_obj.company_id.id,
            'currency_id': journal_obj.company_id.currency_id.id,
            'date_maturity': str(datetime.today().date()),
            'operating_unit_id': for_branch.id,
            'fees_collection_id': collection_id.id,
        }))

        move_lines2.append((0, 0, {
            'name': at_branch.debit_account_id.name,
            'debit': amount_paid,
            'credit': 0,
            # 'account_id': student_obj.property_account_receivable_id.id,# Student account
            # ~ 'account_id': fee_head_obj.contra_account_id.id,# Contra Ledger
            'account_id': at_branch.debit_account_id.id,  # Contra Ledger
            'date': str(datetime.today().date()),
            'partner_id': student_obj.id,
            'journal_id': journal_obj.id,
            'company_id': journal_obj.company_id.id,
            'currency_id': journal_obj.company_id.currency_id.id,  # currency id of narayana
            'date_maturity': str(datetime.today().date()),
            'operating_unit_id': for_branch.id,
            'fees_collection_id': collection_id.id,
        }))

        account_move_obj2 = self.env['account.move'].create({
            'journal_id': journal_obj.id,  # journal ex: sale journal, cash journal, bank journal....
            'date': str(datetime.today().date()),
            'state': 'draft',
            'company_id': journal_obj.company_id.id,
            'operating_unit_id': for_branch.id,
            'line_ids': move_lines2,  # this is one2many field to account.move.line
            'fees_collection_id': collection_id.id,
        })
        account_move_obj2.post()

        ### Entry-3: CO Branch Entry####
        move_lines3 = []

        move_lines3.append((0, 0, {
            'name': at_branch.credit_account_id.name,
            # a label so accountant can understand where this line come from
            'debit': 0,
            'credit': amount_paid,
            'account_id': at_branch.credit_account_id.id,  # Course Fee chart of account.
            'date': str(datetime.today().date()),
            'partner_id': student_obj.id,
            'journal_id': journal_obj.id,  # Cash journal
            'company_id': journal_obj.company_id.id,
            'currency_id': journal_obj.company_id.currency_id.id,
            'date_maturity': str(datetime.today().date()),
            'operating_unit_id': at_branch.id,
            'fees_collection_id': collection_id.id,
        }))
        if not deposit_bank.debit_account_id:
            raise ValidationError('Please configure debit account in bank mapping')
        bank_ac = deposit_bank.debit_account_id
        move_lines3.append((0, 0, {
            'name': bank_ac.name,
            'debit': amount_paid,
            'credit': 0,
            # 'account_id': student_obj.property_account_receivable_id.id,# Student account
            # ~ 'account_id': fee_head_obj.contra_account_id.id,# Contra Ledger
            'account_id': bank_ac.id,  # Contra Ledger
            'date': str(datetime.today().date()),
            'partner_id': student_obj.id,
            'journal_id': journal_obj.id,
            'company_id': journal_obj.company_id.id,
            'currency_id': journal_obj.company_id.currency_id.id,  # currency id of narayana
            'date_maturity': str(datetime.today().date()),
            'operating_unit_id': at_branch.parent_id.id,
            'fees_collection_id': collection_id.id,
            'bank_id': deposit_bank.id
        }))
        account_move_obj3 = self.env['account.move'].create({
            'journal_id': journal_obj.id,  # journal ex: sale journal, cash journal, bank journal....
            'date': str(datetime.today().date()),
            'state': 'draft',
            'company_id': journal_obj.company_id.id,
            'operating_unit_id': at_branch.parent_id.id,
            'line_ids': move_lines3,  # this is one2many field to account.move.line
            'fees_collection_id': collection_id.id,
        })
        account_move_obj3.post()
        return True

    
    
class Bank_Deposit_Clearance_Line(models.Model):
    _name = 'bank.deposit.clearance.line'

    receipt_id =  fields.Many2one('pappaya.fees.receipt','Receipt')
    is_select = fields.Boolean(string='Select')
#     name =  fields.Char('Fee Receipt')
#     enrollment_number = fields.Char('Enrollment Number')
#     grade_id = fields.Many2one('pappaya.grade', 'Class', required=1)
#     student_id = fields.Many2one('pappaya.student', 'Student')
    receipt_date = fields.Date('Receipt Date', related='receipt_id.receipt_date')
    payment_mode_id = fields.Many2one('pappaya.paymode','Payment Mode')
    cheque_dd = fields.Char('Cheque/DD Ref. No', related='receipt_id.cheque_dd')
    cheque_date = fields.Date('Cheque Date', related='receipt_id.cheque_date')
    cheque_mode = fields.Boolean('Is Cheque Mode')
    #total = fields.Float('Total')
    total = fields.Float(related='receipt_id.total', string='Total')
    state = fields.Selection([('draft','In hand'),('deposit','Deposited')],string='Status', default="draft")
    receipt_status = fields.Selection([('cleared','Cleared'),('uncleared','Uncleared')], string='Status', default='uncleared')
    attachment = fields.Binary(string="Attachment")
    
    late_reason = fields.Text('Deposited Late Reason',size=300)
    file_name = fields.Char('Attachment',size=100)
    bank_clearance_id = fields.Many2one('bank.deposit.clearance', string='Bank Deposit Clearance')
    read_only = fields.Boolean(string="Read Only?")

    @api.multi
    def _attachment_limit_check(self, vals):
        if vals:
            if (len(str(vals)) / 1024 /1024) > 5:
                raise ValidationError('Attachment size cannot exceed 5MB')
    @api.multi
    def write(self, vals):
        if 'attachment' in vals.keys() and vals.get('attachment'):
            self._attachment_limit_check(vals['attachment'])
        return super(Bank_Deposit_Clearance_Line, self).write(vals)

    @api.model
    def create(self, vals):
        if 'attachment' in vals.keys() and vals.get('attachment'):
            self._attachment_limit_check(vals['attachment'])
        return super(Bank_Deposit_Clearance_Line, self).create(vals)
    
    
class PaymentStatusLine(models.Model):
    _name = 'payment.status.line'

    receipt_id =  fields.Many2one('pappaya.fees.receipt','Receipt')
    is_select = fields.Boolean(string='Select')
#     name =  fields.Char('Fee Receipt')
#     enrollment_number = fields.Char('Enrollment Number')
#     grade_id = fields.Many2one('pappaya.grade', 'Class', required=1)
#     student_id = fields.Many2one('pappaya.student', 'Student')
    receipt_date = fields.Date('Receipt Date')
    payment_mode_id = fields.Many2one('pappaya.paymode','Payment Mode') 
    cheque_dd = fields.Char('Cheque/DD/POS/Ref. No',size=256)
    cheque_date = fields.Date('Cheque Date')
    #total = fields.Float('Total')
    total = fields.Float(related='receipt_id.total', string='Total')
    #state = fields.Selection([('draft','Draft'),('deposit','Deposited')],string='Status', default="draft")
    state = fields.Selection([('cleared','Cleared'),('uncleared','Uncleared'),('rejected','Rejected')], string='Status', default='uncleared')
    attachment = fields.Binary(string="Attachment")
    file_name = fields.Char('Attachment',size=100)
    bank_clearance_id = fields.Many2one('bank.deposit.clearance', string='Bank Deposit Clearance')
    read_only = fields.Boolean(string="Read Only?")
    read_only1 = fields.Boolean(string="Read Only?")
    remarks = fields.Text(string='Remarks',size=300)
    reason = fields.Text(string='Reason',size=300)
    clear_date = fields.Date('Clearance Date', default=lambda self:fields.Date.today())

    @api.onchange('cheque_dd')
    def onchange_cheque_dd(self):
        for rec in self:
            if rec.cheque_dd:
                cheque_dd = re.match('^[\d]*$', rec.cheque_dd)
                if not cheque_dd:
                    raise ValidationError(_("Please enter a valid Cheque/DD/POS/Ref. No"))

    @api.onchange('clear_date')
    def onchange_clear_date(self):
        if not self.clear_date:
            raise ValidationError("Please enter 'Clearance Date'")
        if self.clear_date and self.clear_date > str(datetime.today().date()):
            raise ValidationError("Clearance Date should not be in future date..!")
        if self.clear_date and self.clear_date < self.cheque_date:
            raise ValidationError("Clearance Date should greater than Cheque Date..!")

    @api.multi
    def _attachment_limit_check(self, vals):
        if vals:
            if (len(str(vals)) / 1024 /1024) > 5:
                raise ValidationError('Attachment size cannot exceed 5MB')
    @api.multi
    def write(self, vals):
        if 'attachment' in vals.keys() and vals.get('attachment'):
            self._attachment_limit_check(vals['attachment'])
        return super(PaymentStatusLine, self).write(vals)

    @api.model
    def create(self, vals):
        if 'attachment' in vals.keys() and vals.get('attachment'):
            self._attachment_limit_check(vals['attachment'])
        return super(PaymentStatusLine, self).create(vals)
    
    @api.multi
    def confirm_cleared(self):
        for record in self:
            record.is_select = True
            if not record.clear_date:
                raise ValidationError("Please enter 'Clearance Date'")
            if record.clear_date and record.clear_date > str(datetime.today().date()):
                    raise ValidationError("Clearance Date should not be in future date..!")
            if record.cheque_date:
                if record.clear_date and record.clear_date < record.cheque_date:
                    raise ValidationError("Clearance Date should greater than Cheque Date..!")
            record.read_only1 = True
            record.bank_clearance_id.confirm_cleared(record.bank_clearance_id)
            
    @api.multi
    def confirm_rejected(self):
        for record in self:
            record.is_select = True
            if not record.remarks:
                raise ValidationError("Please enter 'Remarks'")
            record.read_only1 = True
            record.bank_clearance_id.confirm_rejected(record.bank_clearance_id)
