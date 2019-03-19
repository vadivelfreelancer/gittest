# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError
from datetime import datetime, date
import re


class PappayaFeesReceipt(models.Model):
    _name = 'pappaya.fees.receipt'

    fee_collection_id = fields.Many2one('pappaya.fees.collection', 'Collection ID')
    school_id = fields.Many2one('operating.unit', 'Branch')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    fees_receipt_line =  fields.One2many('pappaya.fees.receipt.line','receipt_id','Receipt Line')
    receipt_date = fields.Date('Receipt Date')
    receipt_no = fields.Char('Receipt No', copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('pappaya.fees.receipt') or _('New'))
    payment_mode_id = fields.Many2one('pappaya.paymode', 'Payment Mode')
    transaction_type = fields.Many2one('pappaya.master','Transaction Type')
    is_show_card_details = fields.Boolean('Show Card Details')
    is_show_cheque_dd_details = fields.Boolean('Is Show Cheque Details')    
    # Card Details
    card_holder_name = fields.Char('Card Holder Name',size=100)
    card_number = fields.Char('Card Number',size=20)
    # card_type = fields.Many2one('pappaya.master','Card Type')
    card_type = fields.Char('Card Type')
    bank_machine_id = fields.Many2one('bank.machine', 'Bank Machine')
    bank_machine_type_id = fields.Many2one('pappaya.master','Bank Machine Type',related='bank_machine_id.bank_machine_type_id')
    # mid_no = fields.Char('M.I.D.No(last 6 digits)',size=30)
    mid_no = fields.Many2one('pappaya.ezetap.device', 'M.I.D.No', )
    tid_no = fields.Char('T.I.D.No',size=30)
    # Cheque Details
    cheque_dd = fields.Char('Cheque/DD No', size=30)
    cheque_date = fields.Date('Cheque Date')
    bank_name = fields.Many2one('res.bank','Bank Name')
    remarks = fields.Text('Remarks' ,size=200)
    total = fields.Float('Total', compute ='compute_total', store=True)
    state = fields.Selection([('paid', 'Paid'),('cancel','Cancel')],string='Status')
    receipt_status = fields.Selection([('cleared','Cleared'),('uncleared','Uncleared')], string='Clearance Status', default='uncleared')
    receipt_type = fields.Selection([('receivable','Receivable'),('payable','Payable')], string='Receipt Type', default='receivable')
    enquiry_id = fields.Many2one('pappaya.admission', 'Admission')
    is_all_adj = fields.Boolean(string='Is All Res Adjustment?', compute='compute_all_course')
    pos_reference_no = fields.Char('POS Ref No.')
    pos_api_response = fields.Text('POS API Response')
    # Chellan Fields
    
    ibank_transaction_id = fields.Char('IBANK TRANSACTION ID')
    instrument_no=fields.Char('INSTRUMENT NUMBER')
    instrument_date =fields.Date('INSTRUMENT DATE')
    pay_mode = fields.Selection([('C','C'),('F','F'),('L','L')], 'Pay Mode')
    transaction_date= fields.Date('TRANSACTION DATE')
    isure_id = fields.Char('ISURE ID')
    micr_code = fields.Char('MICR CODE')
    bank_name_char= fields.Char('Bank Name')
    branch_name= fields.Char('Branch Name')
    client_code = fields.Char('Client Code')
    virtual_acc_no = fields.Char('Virtual Acc No')
    ifsc_code = fields.Char('IFSC')
    paytm_order_ref = fields.Char('PayTM Order ID')

    @api.onchange('cheque_dd')
    def onchange_cheque_dd(self):
        for rec in self:
            if rec.cheque_dd:
                cheque_dd = re.match('^[\d]*$', rec.cheque_dd)
                if not cheque_dd:
                    raise ValidationError(_("Please enter a valid Cheque/DD Ref. No"))
    
    @api.depends('fees_receipt_line')
    def compute_all_course(self):
        cnt = 0
        line_cnt = (len(self.fees_receipt_line.ids))
        for rec in self.fees_receipt_line:
            if rec.total_paid == 0:
                cnt += 1
        if cnt == line_cnt:
            self.is_all_adj = True

    @api.onchange('payment_mode_id')
    def onchange_payment_mode_id(self):
        self.is_show_card_details = True if self.payment_mode_id.is_card else False
        self.is_show_cheque_dd_details = True if self.payment_mode_id.is_cheque else False
    
    @api.multi
    def get_value(self):
        mode_dict = {'cash': 'Cash','cheque/dd':'Cheque', 'dd':'DD','neft/rtgs':'Neft/RTGS','card':'PoS','paytm':'Paytm','payumoney':'PayUmoney'}
        payment_mode = ''
        if self.payment_mode and self.payment_mode in ['cash','card','neft/rtgs']:
            payment_mode = mode_dict[self.payment_mode]
        if self.payment_mode and self.payment_mode in ['cheque/dd','dd']:
            payment_mode = mode_dict[self.payment_mode] + ' Subject to realisation'
        return payment_mode

    @api.multi
    def amount_to_text_in(self, amount, currency):
        return ""
        # convert_amount_in_words2 = amount_to_text_en.amount_to_text(amount, lang='en', currency='')
        # convert_change_in_words = convert_amount_in_words2.split(' and')[1]
        # convert_change_in_words2 = convert_change_in_words.split(' Cent')[0] + ' Paise Only'
        # if "Zero" in convert_amount_in_words2:
        #     convert_amount_in_words2 = convert_amount_in_words2.split(' and')[0] + ' Rupees Only'
        # else:
        #     convert_amount_in_words2 = convert_amount_in_words2.split(' and')[0] + ' Rupees and ' + convert_change_in_words2
        # return convert_amount_in_words2
    
    @api.multi
    def next_due_date_and_payment_details(self):
        data = []
        for record in self.fee_collection_id:
            for rec_line in record.fees_collection_line:
                if rec_line.due_amount and rec_line.term_state in ['due','unclear']:
                    date = ''
                    data.append({
                        'fee_type':rec_line.name.name,
                        'due_amount':rec_line.due_amount,
                        'due_date':date
                        })
        return data 
    
    @api.multi
    def get_school(self):
        school_list = []
        if self.school_id:
            vals = {}
            vals['school_id'] = self.school_id.name
            vals['logo'] = self.school_id.logo
            vals['street'] = self.school_id.tem_street if self.school_id.tem_street else ''
            vals['street2'] = self.school_id.tem_street2 if self.school_id.tem_street2 else ''
            vals['city'] = self.school_id.tem_city_id.id if self.school_id.tem_city_id else ''
            vals['zip'] = self.school_id.tem_zip if self.school_id.tem_zip else ''
            vals['phone'] = self.school_id.phone if self.school_id.phone else ''
            vals['fax'] = self.school_id.fax_id if self.school_id.fax_id else ''
            vals['email'] = self.school_id.email if self.school_id.email else ''
            vals['website'] = self.school_id.website if self.school_id.website else ''
            school_list.append(vals)
        return school_list
    
    @api.multi
    @api.depends('fees_receipt_line.amount')
    def compute_total(self):
        for rec in self:
            rec.total = sum(line.total_paid for line in rec.fees_receipt_line )

    @api.multi
    def generate_receipt_report(self):
        if self._context.get('active_ids'):
            return self.env.ref('pappaya_fees.print_fee_receipt_original').get_report_action(self)
        if not self._context.get('active_ids'):
            # self.get_receipt_data()
            return self.env.ref('pappaya_fees.print_fee_receipt_duplicate').get_report_action(self)


    @api.multi
    def get_receipt_data(self):
        data_list = []
        for rec in self:
            vals = {}
            vals['receipt_ids'] = []
            entity_list = []
            for recline in rec.fees_receipt_line:
                if recline.name.entity_id.id:
                    entity_list.append(recline.name.entity_id.id)
                elif rec.school_id.parent_id.id:
                    entity_list.append(rec.school_id.parent_id.id)
            for entity in set(entity_list):
                rvals = {}
                for line in self.env['pappaya.fees.receipt.line'].search([('receipt_id','=',rec.id)]):
                    if (line.name.entity_id and line.name.entity_id.id == entity) or (line.name and line.receipt_id.school_id.parent_id.id == entity):
                        rvals['branch'] = rec.school_id.name if rec.school_id.name else ''
                        rvals['entity'] = line.name.entity_id.name if line.name.entity_id.name else rec.school_id.parent_id.name
                        rvals['receipt_no'] = rec.receipt_no if rec.receipt_no else ''
                        rvals['date'] = datetime.strptime(str(rec.receipt_date), DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y") if rec.receipt_date else ''
                        rvals['res_no'] = rec.admission_number if rec.admission_number else rec.name.application_no
                        rvals['trans_type'] = rec.transaction_type.name if rec.transaction_type.name else ''
                        rvals['student'] = rec.name.student_full_name if rec.name.student_full_name else ''
                        rvals['father'] = rec.name.father_name if rec.name.father_name else ''
                        rvals['code'] = rec.name.package_id.name if rec.name.package_id.name else ''
                        rvals['pay_mode'] = rec.payment_mode_id.name if rec.payment_mode_id.name else ''
                        rvals['cheque_no'] = rec.cheque_dd if rec.cheque_dd else ''
                        rvals['cheque_date'] = datetime.strptime(str(rec.cheque_date), DEFAULT_SERVER_DATE_FORMAT).strftime("%d/%m/%Y") if rec.cheque_date else ''
                        rvals['bank_name'] = rec.bank_name.name if rec.bank_name.name else ''
                        rvals['virtual_acc_no'] = rec.name.virtual_acc_no if rec.name.virtual_acc_no else ''
                        rvals['receipt_line_ids'] = []
                        tamt, ttax, ttot = 0,0,0
                        camt, ctax, ctot = 0,0,0
                        s_no = 0
                        for fee in rec.fees_receipt_line:
                            if not fee.name.is_course_fee_component and (fee.name.entity_id.id == entity or (not fee.name.entity_id and fee.receipt_id.school_id.parent_id.id == entity)):
                                lvals = {}
                                s_no += 1
                                lvals['s_no'] = s_no
                                lvals['fee_head'] = fee.name.name if fee.name.name else ''
                                lvals['amount'] = fee.total_paid if fee.total_paid else fee.res_adj_amt
                                lvals['tax'] = 0.00
                                lvals['total'] = fee.total_paid if fee.total_paid else fee.res_adj_amt
                                tamt += fee.total_paid if fee.total_paid else fee.res_adj_amt
                                ttax += 0.00
                                ttot += fee.total_paid if fee.total_paid else fee.res_adj_amt
                                rvals['receipt_line_ids'].append(lvals)
                            if fee.name.is_course_fee_component and (fee.name.entity_id.id == entity or (not fee.name.entity_id and fee.receipt_id.school_id.parent_id.id == entity)):
                                camt += fee.total_paid if fee.total_paid else fee.res_adj_amt
                                ctax += 0.00
                                ctot += fee.total_paid if fee.total_paid else fee.res_adj_amt
                                tamt += fee.total_paid if fee.total_paid else fee.res_adj_amt
                                ttax += 0.00
                                ttot += fee.total_paid if fee.total_paid else fee.res_adj_amt
                            if fee.name.is_course_fee_component and (fee.name.entity_id.id == entity or (not fee.name.entity_id and fee.receipt_id.school_id.parent_id.id == entity)):
                                lvals = {}
                                s_no += 1
                                lvals['s_no'] = s_no
                                lvals['fee_head'] = 'Course Fees'
                                lvals['amount'] = camt
                                lvals['tax'] = ctax
                                lvals['total'] = ctot
                                rvals['receipt_line_ids'].append(lvals)
                        rvals['tot_amount'] = tamt
                        rvals['tot_tax'] = 0.0
                        rvals['tot_total'] = ttot
                vals['receipt_ids'].append(rvals)
            data_list.append(vals)
        return data_list


class PappayaFeesReceiptLine(models.Model):
    _name = 'pappaya.fees.receipt.line'
    
    name = fields.Many2one('pappaya.fees.head','Fee Type')
    amount = fields.Float('Amount')
    concession_amount = fields.Float('Concession')
    receipt_id = fields.Many2one('pappaya.fees.receipt', 'Receipt')
    concession_type_id = fields.Many2one('pappaya.concession.reason', 'Concession')
    total_paid = fields.Float('Total Paid')
    res_adj_amt = fields.Float('Reservation Adjustment')
    cgst = fields.Float('CGST %')
    sgst = fields.Float('SGST %')
    payment_mode_id = fields.Many2one('pappaya.paymode', 'Payment Mode')
    without_gst_amt = fields.Float('Total without GST')
    fees_coll_line_id = fields.Many2one('student.fees.collection', 'Fees Collection Line')
    fees_coll_line_status = fields.Char('Coll line status')
    other_payment_id = fields.Many2one('pappaya.other.payment', 'Other Payment')
