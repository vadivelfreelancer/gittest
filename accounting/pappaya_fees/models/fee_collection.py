# -*- coding: utf-8 -*-
import logging
import re
import time
from datetime import datetime, date

import requests

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    import cx_Oracle

except ImportError:

    _logger.info(
        "The `cx_Oracle` Python module is not available. "
        "Try `pip3 install cx_Oracle` to install it."
    )




# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}

HEADERS = {'Content-Type': 'application/json'}

INPUT_PARAM = {"username": tools.config.get('user_name'),
               "appKey": tools.config.get('app_key'),
               "orgCode": tools.config.get('org_code')
               }

SMS_CRED_PARAM = {'host': tools.config.get('oracle_host'),
                  'port': tools.config.get('oracle_port'),
                  'database': tools.config.get('oracle_database'),
                  'table': tools.config.get('oracle_table'),
                  'username': tools.config.get('oracle_username'),
                  'password': tools.config.get('oracle_password'),
                  }


class Pappaya_fees_collection(models.Model):
    _name = 'pappaya.fees.collection'

    @api.multi
    def _send_sms(self, mobile, message):
        date_time = datetime.now()
        timestamp = int(time.time())
        try:

            QUERY_INSERT = "INSERT INTO SMS_AUTOMESSAGE(AMSLNO, MOBILENUMBER, MESSAGE, PRIORITY, DATETIME) " \
                           "VALUES(:1, :2, :3, :4, :5)"
            values = (timestamp, mobile, message, 1, date_time)
            dsn = cx_Oracle.makedsn(SMS_CRED_PARAM['host'], SMS_CRED_PARAM['port'], SMS_CRED_PARAM['database'])
            connection = cx_Oracle.connect(SMS_CRED_PARAM['username'] + '/' + SMS_CRED_PARAM['password'] + '@' +
                                           SMS_CRED_PARAM['host'] + ':' + str(SMS_CRED_PARAM['port']) + '/' +
                                           SMS_CRED_PARAM['database'])
            cursor = connection.cursor()
            cursor.execute(QUERY_INSERT, values)
            _logger.info('Query Executed and Values: ' + str(values))
            connection.commit()
            cursor.close()
            connection.close()
        except Exception as e:
            _logger.error('Error connecting to databases: ' + str(e))
        return True

    @api.multi
    def action_send_sms(self):
        mobile = '91' + str(
            self.enquiry_id.mobile_one if self.enquiry_id.mobile_one else self.enquiry_id.mobile_two).strip()
        message = ''
        substitutions = {'$NAME$': str(self.enquiry_id.student_full_name),
                         '$ADM_NO$': str(self.enquiry_id.res_no),
                         '$AMOUNT$': str(self.pay_amount),
                         '$DATE$': str(date.today().strftime('%d-%m-%Y')),
                         }
        substrings = sorted(substitutions, key=len, reverse=True)
        regex = re.compile('|'.join(map(re.escape, substrings)))

        if self.payment_mode_id.is_cash:
            sms_content = self.env['pappaya.sms.content'].search([('type', '=', 'cash'), ('active', '=', True)],
                                                                 limit=1)
            if sms_content:
                message = regex.sub(lambda match: substitutions[match.group(0)], sms_content.description)
            else:
                _logger.info('Unable to send SMS, There is no SMS Content for Cash mode.')

        elif self.payment_mode_id.is_cheque:
            sms_content = self.env['pappaya.sms.content'].search([('type', '=', 'cheque_dd'), ('active', '=', True)],
                                                                 limit=1)
            if sms_content:
                message = regex.sub(lambda match: substitutions[match.group(0)], sms_content.description)
            else:
                _logger.info('Unable to send SMS, There is no SMS Content for Cheque/DD mode.')
        _logger.info('SMS Content: ' + str(message))
        self._send_sms(mobile, message)

        return True

    @api.multi
    def push_to_pay(self):
        if not tools.config.get('user_name'):
            raise ValidationError('Need to configure POS Device Details in Configuration files, Contact Pappaya Support Team')
        input_param = INPUT_PARAM

        input_param['amount'] = str(self.pay_amount)
        input_param['phoneNumber'] = "9876543210"
        # input_param['pushTo'] = {"deviceId": tools.config.get('DEVICEID')}
        input_param['pushTo'] = {"deviceId": self.mid_no.device_id}
        # input_param['emailID'] = ""
        payment_ref_no = self.env['ir.sequence'].next_by_code('pappaya.ezepay.payment.ref')
        input_param['externalRefNumber'] = str(payment_ref_no)
        input_param['externalRefNumber4'] = str(self.pay_amount/2.0) # for NES account
        input_param['externalRefNumber5'] = str(self.pay_amount/2.0) # for NSPIRA account as per discussion with Chankey

        ret_val = {
                'type': 'ir.actions.act_window',
                # 'name': 'Confirmation - Next Stage Process',
                'res_model': 'pappaya.fees.collection',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self.id,
                'view_id': self.env.ref('pappaya_fees.pappaya_fees_collection_form', False).id,
                'target': 'new',
            }

        response = requests.post(tools.config.get('pushapi_url'), headers=HEADERS,
                                 json=input_param)
        resp_cont = response.json()
        if resp_cont:
            if 'success' in resp_cont:
                if resp_cont['success']:
                    self.write({'pos_reference_no':payment_ref_no})
                else:
                    raise ValidationError(resp_cont['message'])
        return ret_val

    @api.multi
    def validate_card_payment(self):
        input_param = INPUT_PARAM
        if not tools.config.get('statusapi_url'):
            raise ValidationError('Need to configure POS Device Details in Configuration files, Contact Pappaya Support Team')
        if not self.pos_reference_no:
            raise ValidationError('Please click the Pay button and swipe the card then proceed')
        receipt_srch = self.env['pappaya.fees.receipt'].sudo().search([('pos_reference_no','=',self.pos_reference_no)])
        if receipt_srch:
            raise ValidationError('Please click the Pay button and swipe the card then proceed')
        input_param['externalRefNumber'] = self.pos_reference_no

        response = requests.post(tools.config.get('statusapi_url'), headers=HEADERS, json=input_param)
        resp_cont = response.json()
        print (resp_cont,"========================= API REsponse ============")
        if 'status' in resp_cont:
            if resp_cont['status'] == 'AUTHORIZED':
            # if resp_cont['status'] == 'REVERSED':
                self.card_type = resp_cont['paymentCardBrand']
                self.card_number= resp_cont['formattedPan']
                self.card_holder_name = resp_cont['nameOnCard']
                self.tid_no = resp_cont['txnId']
                self.pos_api_response = response
                value = self.fee_pay()
                return value
            else:
                raise ValidationError(resp_cont['status'])
        else:
            raise ValidationError(resp_cont['message'])
        return True

    school_id = fields.Many2one('operating.unit', 'Branch')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    fees_collection_line = fields.One2many('student.fees.collection', 'collection_id', 'Collection Line')
    pay_amount = fields.Float('Pay Amount')
    total = fields.Float('Grand Total', compute='compute_total')
    bulk_term_state = fields.Selection([('due', 'Due'), ('paid', 'Paid'),('transfer','Transfer')], 'Status', default='due', compute='compute_state_term')
    payment_mode_id = fields.Many2one('pappaya.paymode', 'Payment Mode')
    payment_mode = fields.Selection([('paytm','Paytm'),('payumoney','PayUmoney'),('cash', 'Cash'), ('cheque/dd', 'Cheque'),('dd', 'DD'), ('neft/rtgs', 'NEFT/RTGS'),('card','POS')], string='Payment Mode')
    transaction_type = fields.Many2one('pappaya.master','Transaction Type')
    # Card Details
    card_holder_name = fields.Char('Card Holder Name',size=100)
    card_number = fields.Char('Card Number',size=20)
    # card_type = fields.Many2one('pappaya.master','Card Type')
    card_type = fields.Char('Card Type')
    bank_machine_id = fields.Many2one('bank.machine', 'Bank Machine')
    bank_machine_type_id = fields.Many2one('pappaya.master','Bank Machine Type',related='bank_machine_id.bank_machine_type_id')
    # mid_no = fields.Char('M.I.D.No(last 6 digits)',size=30)
    mid_no = fields.Many2one('pappaya.ezetap.device','M.I.D.No',)
    tid_no = fields.Char('T.I.D.No',size=30)
    # Cheque Details
    cheque_dd = fields.Char('Cheque/DD Ref. No',size=30)
    bank_name = fields.Many2one('res.bank','Bank Name')
    remarks = fields.Text('Remarks',size=200)
    due_total = fields.Float('Total due', compute='compute_total_due')
    paid_total = fields.Float('Total paid', compute='compute_total_paid')

    collection_date = fields.Date(string="Collection Date",)
    pay_due_total = fields.Float('Pay Due',compute='compute_pay_due')
    partner_id = fields.Many2one('res.partner', 'Partner Name')
    res_adj_amt_total = fields.Float('res_adj_amt_total',compute='compute_res_adj_amt')
    res_adj_amt_extra_total = fields.Float('res_adj_amt_total',compute='compute_res_adj_amt_extra')
    is_show_card_details = fields.Boolean('Show Card Details')
    is_show_cheque_dd_details = fields.Boolean('Is Show Cheque Details')
    admission_cancel = fields.Boolean('Cancel', default=False)
    no_of_cas_transaction = fields.Integer(compute='_compute_no_of_cash_transaction', string='No Of Cash Transaction')
    cheque_date = fields.Date('Cheque Date')
    is_amt = fields.Boolean(string='Is Amount')
    refund_amount = fields.Float('Refund Amount')
    is_refunded = fields.Boolean('Refunded', default=False)
    pos_reference_no = fields.Char('POS Ref No.')
    pos_api_response = fields.Text('POS API Response')
    bank_chellan_id = fields.Many2one('bank.challan.transaction', 'Bank Chellan')
    paytm_order_ref = fields.Char('PayTM Order ID')
    sponsor_paid = fields.Boolean(string='Sponsor Paid', default=False)
    is_res_adjusted = fields.Boolean(compute='_compute_is_res_adjusted', string='Is Reservation Fee Adjusted')
    
    @api.multi
    @api.depends('fees_collection_line')
    def _compute_is_res_adjusted(self):
        for record in self:
            is_res_adjusted = False
            for line in record.fees_collection_line:
                if line.res_adj_amt > 0.0:
                    is_res_adjusted = True
                    break
            self.is_res_adjusted = is_res_adjusted
    
    # @api.onchange('cheque_date')
    # def onchange_cheque_date(self):
    #     cheque_date = datetime.strptime(self.cheque_date, "%Y-%m-%d").date()
    #     if cheque_date < date.today():
    #         raise ValidationError('Please enter valid Cheque Date..!')

    @api.onchange('cheque_dd')
    def onchange_cheque_dd(self):
        for rec in self:
            if rec.cheque_dd:
                cheque_dd = re.match('^[\d]*$', rec.cheque_dd)
                if not cheque_dd:
                    raise ValidationError(_("Please enter a valid Cheque/DD Number"))

    @api.multi
    def _compute_no_of_cash_transaction(self):
        for record in self:
            no_of_cas_transaction = 0
            for receipt in self.env['pappaya.fees.receipt'].sudo().search([('fee_collection_id','=',record.id)]):
                if receipt.payment_mode_id.is_cash:
                    no_of_cas_transaction += 1
            record.no_of_cas_transaction = no_of_cas_transaction

    @api.onchange('transaction_type','pay_amount')
    def onchange_transaction_type(self):
        self.payment_mode_id = False
        if self.pay_amount > 0:
            self.is_amt = True
            domain = {};domain['payment_mode_id'] = [('id','in',[])]
            if self.school_id:
                paymodes=[]
                cash_pay_id = self.env['pappaya.paymode'].search([('is_cash','=',True)])
                device_ids = self.env['pappaya.ezetap.device'].search([('school_ids_m2m','in',self.school_id.id)])
                if self.school_id.is_show_cash_mode:
                    paymodes = self.school_id.paymode_ids.ids
                else:
                    if self.school_id.cash_mode_limit > self.no_of_cas_transaction:
                        if self.school_id.cash_mode_limit == 1:
                            if not self.env['pappaya.fees.receipt'].sudo().search([('fee_collection_id','=',self._origin.id)]).ids:
                                paymodes = self.school_id.paymode_ids.ids
                            else:
                                for paymode in self.school_id.paymode_ids:
                                    if paymode.id != cash_pay_id.id:
                                        paymodes.append(paymode.id)
                    else:
                        for paymode in self.school_id.paymode_ids:
                            if paymode.id != cash_pay_id.id:
                                paymodes.append(paymode.id)
                domain['payment_mode_id'] = [('id','in',paymodes)]
                domain['mid_no'] = [('id','in',device_ids.ids)]
            return {'domain':domain}
        else:
            self.is_amt = False
    
    @api.onchange('payment_mode_id')
    def onchange_payment_mode_id(self):
        self.is_show_card_details = True if self.payment_mode_id.is_card else False
        self.is_show_cheque_dd_details = True if self.payment_mode_id.is_cheque else False
        bank_ids = []; bank_machine_ids = []; bank_machine_type_ids = []
        if self.payment_mode_id.is_card:
            account_mapping_obj = self.env['branch.bank.account.mapping'].search([('operating_unit_id','=',self.school_id.id),('is_card','=',True)], order='id')
            if len(account_mapping_obj.ids) == 1:
                # self.bank_name = account_mapping_obj.bank_id.id;
                self.bank_machine_id = account_mapping_obj.bank_machine_id.id
                self.bank_machine_type_id = account_mapping_obj.bank_machine_type_id.id
                # self.mid_no = account_mapping_obj.mid_number
                # self.tid_no = account_mapping_obj.tid_number
                self.tid_no = ''
            else:
                self.bank_name = self.bank_machine_id = self.bank_machine_type_id =  self.tid_no = False
                # self.mid_no = False
                self.card_type = self.pos_reference_no = ''
            
            for record in account_mapping_obj:
                bank_ids.append(record.bank_id.id)
                bank_machine_ids.append(record.bank_machine_id.id)
                bank_machine_type_ids.append(record.bank_machine_type_id.id)
        if self.payment_mode_id.is_cheque:
            account_mapping_obj = self.env['branch.bank.account.mapping'].search([('operating_unit_id','=',self.school_id.id)], order='id') # ('is_cheque','=',True)
            if len(account_mapping_obj.ids) == 1:
                # self.bank_name = account_mapping_obj.bank_id.id;
                self.bank_machine_id = account_mapping_obj.bank_machine_id.id
                self.bank_machine_type_id = account_mapping_obj.bank_machine_type_id.id
                # self.mid_no = account_mapping_obj.mid_number
                self.tid_no = account_mapping_obj.tid_number
                
            for record in account_mapping_obj:
                # bank_ids.append(record.bank_id.id)
                if record.bank_machine_id.id:
                    bank_machine_ids.append(record.bank_machine_id.id)
                if record.bank_machine_type_id.id:
                    bank_machine_type_ids.append(record.bank_machine_type_id.id)
        
        return {'domain': {#'bank_name': [('id', 'in', bank_ids)],
                           'bank_machine_id': [('id', 'in', bank_machine_ids)],
                           'bank_machine_type_id': [('id', 'in', bank_machine_type_ids)]}}
            
    @api.onchange('bank_name')
    def onchange_bank_name(self):
        if self.bank_name and self.payment_mode_id.is_card:
            account_mapping_id = self.env['branch.bank.account.mapping'].search([('operating_unit_id','=',self.school_id.id),('is_card','=',True),('bank_id','=',self.bank_name.id)], limit=1)
            if account_mapping_id:
                self.bank_name = account_mapping_id.bank_id.id; self.bank_machine_id = account_mapping_id.bank_machine_id.id
                self.bank_machine_type_id = account_mapping_id.bank_machine_type_id.id
                # self.mid_no = account_mapping_id.mid_number
                self.tid_no = account_mapping_id.tid_number
            else:
                self.bank_name = self.bank_machine_id = self.bank_machine_type_id = self.tid_no = False
                # self.mid_no = False
                                
    @api.multi
    def refund_request(self):
        self.status = 'refund_request'
        
    @api.one
    @api.depends('fees_collection_line','pay_due_total')
    def compute_pay_due(self):
        amt = 0.0
        all_paid = True; reservation_paid = 0.0;
        for line in self.fees_collection_line:
            if line.name.is_reservation_fee and not self.is_res_adjusted:
                reservation_paid += line.total_paid
            elif line.name.is_reservation_fee and line.term_state != 'paid':
                reservation_paid += line.total_paid
            if not line.name.is_reservation_fee and not line.name.is_course_fee:
                amt +=  line.due_amount
        amt -= reservation_paid
        if not amt == 0.0:
            all_paid = False
        self.pay_due_total = amt
        if all_paid:
            self.bulk_term_state = 'paid'    
    
    @api.one        
    @api.depends('fees_collection_line.term_state','bulk_term_state')
    def compute_state_term(self):
        all_paid = True
        transfer = False
        for line in self.fees_collection_line:
            if line.term_state in ['due','processing']:
                all_paid = False
            if line.term_state == 'transfer':
                transfer = True
        if all_paid:
            self.bulk_term_state = 'paid'
        elif transfer:
            self.bulk_term_state = 'transfer'
        else:
            self.bulk_term_state = 'due' 
    
    # @api.multi
    # @api.constrains('collection_date')
    # def collection_date_validation(self):
    #     for r in self:
    #         if r.academic_year_id.start_date:
    #             if r.collection_date and r.collection_date >= r.academic_year_id.start_date and r.collection_date > str(datetime.today().date()):
    #                 raise ValidationError("Collection should not be in future date.!")
    #

    # @api.one
    # @api.constrains('collection_date')
    # def _check_collection_date(self):
    #     if self.collection_date and self.collection_date < self.academic_year_id.start_date or self.collection_date > self.academic_year_id.end_date:
    #         raise ValidationError('Collection Date should be within the academic year..!')


    @api.multi
    @api.depends('fees_collection_line.amount')
    def compute_total(self):
        for rec in self:
            tot = 0.0
            for line in rec.fees_collection_line:
                if line.name.is_course_fee or line.name.is_reservation_fee:
                    tot += line.amount
            total = round(sum(line.amount for line in rec.fees_collection_line ))
            rec.total = total - tot

    @api.multi
    @api.depends('fees_collection_line.due_amount')
    def compute_total_due(self):
        for rec in self:
            due_tot = 0.0
            for line in rec.fees_collection_line:
                if not (line.name.is_course_fee or line.name.is_reservation_fee):
                    due_tot += line.due_amount
            total = round(sum(line.due_amount for line in rec.fees_collection_line))
            if due_tot > 0 and self.enquiry_id.stage_id.sequence == 4:
                rec.due_total = total - due_tot
            if due_tot > 0 and self.enquiry_id.stage_id.sequence != 4:
                rec.due_total = due_tot - rec.paid_total

    @api.multi
    @api.depends('fees_collection_line.total_paid')     
    def compute_total_paid(self):
        amt = 0.0
        reservation_paid = 0.0;
        for line in self.fees_collection_line:
            if line.name.is_reservation_fee and not self.is_res_adjusted:
                reservation_paid += line.total_paid
            elif line.name.is_reservation_fee and line.term_state != 'paid':
                reservation_paid += line.total_paid
                
            if not line.name.is_reservation_fee and not line.name.is_course_fee:
                amt +=  line.total_paid
        amt += reservation_paid
        
        self.paid_total = amt

    @api.multi
    @api.depends('fees_collection_line.res_adj_amt')
    def compute_res_adj_amt(self):
        for rec in self:
            rec.res_adj_amt_total = round(sum(line.res_adj_amt for line in rec.fees_collection_line))
            
    @api.multi
    @api.depends('fees_collection_line.res_adj_amt_extra')
    def compute_res_adj_amt_extra(self):
        for rec in self:
            rec.res_adj_amt_extra_total = round(sum(line.res_adj_amt_extra for line in rec.fees_collection_line))
    
    @api.constrains('pay_amount')
    def _check_pay_amount(self):
        if self.pay_amount < 0.0:
            raise ValidationError(_("The value of amount should be positive !"))

    @api.onchange('pay_amount')
    def _onchange_pay_amount(self):
        if self.pay_amount:
            self._check_pay_amount()

        
    @api.multi
    def _get_move_lines(self, student_obj, fee_head_obj, amount_paid, journal_obj, operating_unit_obj):
        move_lines = []
        if self.payment_mode_id.is_cash:
            if not self.payment_mode_id.debit_account_id:
                raise ValidationError('Please configure Debit account in payment mode')
            debit_acc_id = self.payment_mode_id.debit_account_id
            move_lines.append((0, 0, {
                'name': fee_head_obj.name, # a label so accountant can understand where this line come from
                'debit': 0,
                'credit': amount_paid,
                'account_id': fee_head_obj.credit_account_id.id, # Course Fee chart of account.
                'date': str(datetime.today().date()),
                'partner_id': student_obj.id,
                'journal_id': journal_obj.id, #  Cash journal
                'company_id': journal_obj.company_id.id,
                'currency_id': journal_obj.company_id.currency_id.id,
                'date_maturity': str(datetime.today().date()),
                'operating_unit_id': operating_unit_obj.id,
                'fees_collection_id': self.id,
                }))
            move_lines.append((0, 0, {
                'name': student_obj.name,
                'debit': amount_paid,
                'credit': 0,
                #'account_id': student_obj.property_account_receivable_id.id,# Student account
                # ~ 'account_id': fee_head_obj.contra_account_id.id,# Contra Ledger
                'account_id': debit_acc_id.id,# Contra Ledger
                'date': str(datetime.today().date()),
                'partner_id': student_obj.id,
                'journal_id': journal_obj.id,
                'company_id': journal_obj.company_id.id,
                'currency_id': journal_obj.company_id.currency_id.id, # currency id of narayana
                'date_maturity': str(datetime.today().date()),
                'operating_unit_id': operating_unit_obj.id,
                'fees_collection_id': self.id,
                }))
            return move_lines
    
    @api.multi
    def _create_move_entry(self, journal_obj, operating_unit_obj, line_ids):
        account_move_obj = self.env['account.move'].create({
            'journal_id': journal_obj.id, # journal ex: sale journal, cash journal, bank journal....
            'date': str(datetime.today().date()),
            'state': 'draft',
            'company_id': journal_obj.company_id.id,
            'operating_unit_id': operating_unit_obj.id,
            'line_ids': line_ids, # this is one2many field to account.move.line
            })
        return account_move_obj
    
    """ Other Payment Entries """
    
    @api.multi
    def fee_pay_other_payment(self):
        receipt_id = False        
        if 'other_payment' in self._context and self._context['other_payment']:
            for record in self:
                status = 'paid' if record.payment_mode_id.is_cash else 'processing'
                pay_amount = record.pay_amount
                # Other Payments to be paid
                total_amount_to_be_paid = 0.0
                if 'active_model' in self._context and self._context['active_model'] == 'pappaya.other.payment':
                    other_pay_obj = self.env['pappaya.other.payment'].sudo().search([('id','in',self._context['active_ids'] or [])], limit=1)
                    total_amount_to_be_paid = other_pay_obj.amount
                if record.pay_amount == 0.0 or total_amount_to_be_paid != pay_amount:
                    raise ValidationError("Pay actual amount")
                for line in record.fees_collection_line:
                    if line.term_state == 'due' and line.due_amount > 0.00 and pay_amount > 0.00 and line.name.id == other_pay_obj.payment_head.id:
                        cgst = 0.00; sgst = 0.00; without_gst_amt = 0.00;
                        cgst_percentage = (100 * line.cgst)/line.amount; sgst_percentage = (100 * line.sgst)/line.amount
                        cgst = (cgst_percentage * line.due_amount)/100; sgst = (sgst_percentage * line.due_amount)/100
                        without_gst_amt =  line.due_amount - (cgst + sgst)
                        # Receipt Creation
                        if line.due_amount == pay_amount:
                            line.total_paid = line.total_paid + pay_amount
                            line.term_state = status
                        else:
                            line.total_paid = line.total_paid + pay_amount
                            line.term_state = 'due'

                        receipt_id = self.env['pappaya.fees.receipt'].sudo().create({
                                                         'state':'paid',
                                                         'fee_collection_id':record.id,
                                                         'school_id' : record.school_id.id,
                                                         'academic_year_id' : record.academic_year_id.id,
                                                         'enquiry_id':record.enquiry_id.id,
                                                         'payment_mode_id': record.payment_mode_id.id,
                                                         'transaction_type': record.transaction_type.id,
                                                         'is_show_card_details':record.is_show_card_details,
                                                         'is_show_cheque_dd_details': record.is_show_cheque_dd_details,
                                                         'bank_machine_id': record.bank_machine_id.id,
                                                         'bank_machine_type_id':record.bank_machine_type_id.id,
                                                         'card_holder_name': record.card_holder_name,
                                                         'card_number': record.card_number,
                                                         'card_type': record.card_type,
                                                         'mid_no': record.mid_no.id,
                                                         'tid_no': record.tid_no,
                                                         'cheque_dd' : record.cheque_dd,
                                                         'cheque_date' : record.cheque_date,
                                                         'bank_name':record.bank_name.id,
                                                         'remarks':record.remarks,
                                                         'receipt_date':record.collection_date,
                                                         'receipt_status':'cleared',
                                                         'pos_reference_no': record.pos_reference_no,
                                                         'pos_api_response': record.pos_api_response
                                                       })
                           
                        if receipt_id:
                            receipt_id.write({'virtual_acc_no':self.enquiry_id.virtual_acc_no, 'ifsc_code':'KKBK0000552'})
                            receipt_line = self.env['pappaya.fees.receipt.line'].create({
                                'receipt_id': receipt_id.id,
                                'name':line.name.id,
                                'amount':pay_amount,
                                'concession_amount':line.concession_amount,
                                'concession_type_id':line.concession_type_id,
                                'cgst':cgst,'sgst':sgst,'without_gst_amt':without_gst_amt,
                                'total_paid':pay_amount,
                                'fees_coll_line_id': line.id,
                                'fees_coll_line_status': 'paid',
                                'other_payment_id':other_pay_obj.id
                                })
                            if not record.payment_mode_id.is_cash:
                                receipt_id.receipt_status = 'uncleared'
                        # Ledger Creation
                        ledger_id = self.env['pappaya.fees.ledger'].search([('academic_year_id','=',record.academic_year_id.id),('enquiry_id','=',record.enquiry_id.id)], limit=1)
                        if ledger_id:
                            fees_ledger_line = self.env['pappaya.fees.ledger.line'].search([('name','=',line.name.name),('fee_line_id','=',line.id)])
                            if not fees_ledger_line:
                                self.env['pappaya.fees.ledger.line'].create({
                                    'fees_ledger_id':ledger_id.id,
                                    'fee_line_id':line.id,
                                    'name':line.name.name,
                                    'credit':line.amount,
                                    'concession_amount':line.concession_amount,
                                    'concession_type_id':line.concession_type_id.id,
                                    'debit':0.0,
                                    'balance':0.0,
                                })
                            else:
                                fees_ledger_line.credit += line.amount; 
                                
                            self.env['pappaya.fees.receipt.ledger'].create({
                                'fees_ledger_id': ledger_id.id,
                                'fees_receipt_id': receipt_id.id,
                                'name':receipt_id.receipt_no,
                                'posting_date':receipt_id.receipt_date,
                                'fees_head':receipt_line.name.name,
                                'transaction':receipt_id.remarks,
                                'concession_amount':receipt_line.concession_amount,
                                'payment_mode_id':receipt_id.payment_mode_id.id,
                                'amount':receipt_line.total_paid,
                            })
                            
                        # Account Moves Creation
                        journal_obj = self.env['account.journal'].search([('code', '=', 'NARFC')])
                        if not record.enquiry_id.partner_id:
                            stu_name = record.enquiry_id.student_full_name
                            partner_obj = self.env['res.partner'].create({'name': stu_name,'company_type': 'person','company_id': self.env.user.company_id.id,'school_id':record.school_id.id})
                            record.enquiry_id.partner_id = record.partner_id = partner_obj.id
                        
                        if self.payment_mode_id.is_cash:
                            line_ids = self._get_move_lines(record.enquiry_id.partner_id, line.name, pay_amount, journal_obj, record.school_id)
                            account_move = self._create_move_entry(journal_obj, record.school_id, line_ids)
                            account_move.post()
                        
                        pay_amount -= pay_amount    


            other_payment_id = self._context.get('other_payment') or False
            if other_payment_id:
                other_payment_obj = self.env['pappaya.other.payment'].search([('id','=',other_payment_id)])
                if other_payment_obj:
                    other_payment_obj.payment_mode_id = record.payment_mode_id.id;other_payment_obj.transaction_type = record.transaction_type.id
                    other_payment_obj.card_holder_name = record.card_holder_name; other_payment_obj.card_number = record.card_number
                    other_payment_obj.card_type = record.card_type; other_payment_obj.bank_machine_id = record.bank_machine_id.id
                    other_payment_obj.bank_machine_type_id = record.bank_machine_type_id.id; other_payment_obj.mid_no = record.mid_no.id
                    other_payment_obj.tid_no = record.tid_no; other_payment_obj.cheque_dd = record.cheque_dd; other_payment_obj.cheque_date = record.cheque_date; other_payment_obj.bank_name = record.bank_name.id
                    other_payment_obj.is_show_card_details = record.is_show_card_details; other_payment_obj.is_show_cheque_dd_details = record.is_show_cheque_dd_details
                    other_pay_obj.pos_reference_no = record.pos_reference_no; other_pay_obj.receipt_id = receipt_id.id
                    other_pay_obj.pos_api_response = record.pos_api_response
                    if self._compute_other_payment_paid(record.fees_collection_line, other_payment_obj):
                        other_payment_obj.is_paid = True
                        other_payment_obj.state = status
            # ############### SMS Integration ###################
            if self.payment_mode_id.is_cash or self.payment_mode_id.is_cheque:
                self.action_send_sms()
            # ############### END ###############################
            record.payment_mode_id = record.is_show_card_details = record.is_show_cheque_dd_details = record.transaction_type = record.bank_machine_id = record.bank_machine_type_id = record.bank_name = False
            record.card_holder_name = record.card_number = record.card_type = record.tid_no = record.cheque_dd = ''
            record.mid_no = None
            record.pos_reference_no = ''
            record.cheque_date = None
            record.pay_amount = 0.00;record.remarks = None;record.collection_date = datetime.now().date()
        
            form_view = self.env.ref('pappaya_fees.pappaya_fees_receipt_form')
            tree_view = self.env.ref('pappaya_fees.pappaya_fees_receipt_tree')
            if receipt_id:
                value = {
                    'domain': str([('id', '=', receipt_id.id)]),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'name':'Fee receipt',
                    'res_model': 'pappaya.fees.receipt',
                    'view_id': False,
                    'views': [(form_view and form_view.id or False, 'form'),
                               (tree_view and tree_view.id or False, 'tree')],
                    'type': 'ir.actions.act_window',
                    'res_id': receipt_id.id,
                    'target': 'new',
                    'nodestroy': True
                 }
                
                return value

    # Pocket Money Fee Payment

    @api.multi
    def fee_pocket_money_payment(self):
        receipt_id = False
        if 'pocket_money_payment' in self._context and self._context['pocket_money_payment']:
            for record in self:
                status = 'paid' if record.payment_mode_id.is_cash else 'processing'
                pay_amount = record.pay_amount
                line_amount, total_line_amount = 0.0, 0.0
                for rec in self.fees_collection_line:
                    if rec.name.is_pocket_money:
                        line_amount = rec.due_amount
                        total_line_amount = rec.gst_total
                if 'active_model' in self._context and self._context['active_model'] == 'pappaya.pocket.money':
                    pocket_money_obj = self.env['pappaya.pocket.money'].sudo().search([('id','in',self._context['active_ids'] or [])], limit=1)
                if record.pay_amount == 0.0 or line_amount != pay_amount:
                    raise ValidationError("Pay actual amount")
                for line in record.fees_collection_line:
                    if line.term_state == 'due' and line.due_amount > 0.00 and pay_amount > 0.00 and line.name.is_pocket_money:
                        cgst = 0.00;
                        sgst = 0.00;
                        without_gst_amt = 0.00;
                        cgst_percentage = (100 * line.cgst) / line_amount;
                        sgst_percentage = (100 * line.sgst) / line_amount
                        cgst = (cgst_percentage * line.due_amount) / 100;
                        sgst = (sgst_percentage * line.due_amount) / 100
                        without_gst_amt = line.due_amount - (cgst + sgst)
                        # Receipt Creation
                        if line.due_amount == pay_amount:
                            line.total_paid = line.total_paid + pay_amount
                            line.term_state = status
                        else:
                            line.total_paid = line.total_paid + pay_amount
                            line.term_state = 'due'

                        receipt_id = self.env['pappaya.fees.receipt'].sudo().create({
                            'state': 'paid',
                            'fee_collection_id': record.id,
                            'school_id': record.school_id.id,
                            'academic_year_id': record.academic_year_id.id,
                            'enquiry_id': record.enquiry_id.id,
                            'payment_mode_id': record.payment_mode_id.id,
                            'transaction_type': record.transaction_type.id,
                            'is_show_card_details': record.is_show_card_details,
                            'is_show_cheque_dd_details': record.is_show_cheque_dd_details,
                            'bank_machine_id': record.bank_machine_id.id,
                            'bank_machine_type_id': record.bank_machine_type_id.id,
                            'card_holder_name': record.card_holder_name,
                            'card_number': record.card_number,
                            'card_type': record.card_type,
                            'mid_no': record.mid_no.id,
                            'tid_no': record.tid_no,
                            'cheque_dd': record.cheque_dd,
                            'cheque_date': record.cheque_date,
                            'bank_name': record.bank_name.id,
                            'remarks': record.remarks,
                            'receipt_date': record.collection_date,
                            'receipt_status': 'cleared',
                            'pos_reference_no': record.pos_reference_no,
                            'pos_api_response': record.pos_api_response
                        })
                        if receipt_id:
                            receipt_line = self.env['pappaya.fees.receipt.line'].create({
                                'receipt_id': receipt_id.id,
                                'name': line.name.id,
                                'amount': pay_amount,
                                'concession_amount': line.concession_amount,
                                'concession_type_id': line.concession_type_id,
                                'cgst': cgst, 'sgst': sgst,
                                'without_gst_amt': without_gst_amt,
                                'total_paid': pay_amount,
                                'fees_coll_line_status': 'paid',
                                'pocket_money_id': pocket_money_obj.id,
                                'fees_coll_line_id': line.id
                            })
                            if not record.payment_mode_id.is_cash:
                                receipt_id.receipt_status = 'uncleared'
                        # Ledger Creation
                        ledger_id = self.env['pappaya.fees.ledger'].search([('fee_collection_id', '=', record.id)])
                        if ledger_id:
                            ledger_line = self.env['pappaya.fees.ledger.line'].search(
                                [('fees_ledger_id', '=', ledger_id.id), ('name', '=', line.name.name)])
                            if not ledger_line:
                                self.env['pappaya.fees.ledger.line'].create({
                                    'fees_ledger_id': ledger_id.id,
                                    'fee_line_id': line.id,
                                    'name': line.name.name,
                                    'credit': line_amount,
                                    'concession_amount': line.concession_amount,
                                    'concession_type_id': line.concession_type_id.id,
                                    'debit': 0.0,
                                    'balance': 0.0,
                                })
                            else:
                                ledger_line.credit = total_line_amount
                                ledger_line.debit = line.total_paid
                            self.env['pappaya.fees.receipt.ledger'].create({
                                'fees_ledger_id': ledger_id.id,
                                'fees_receipt_id': receipt_id.id,
                                'name': receipt_id.receipt_no,
                                'posting_date': receipt_id.receipt_date,
                                'fees_head': receipt_line.name.name,
                                'transaction': receipt_id.remarks,
                                'concession_amount': receipt_line.concession_amount,
                                'payment_mode_id': receipt_id.payment_mode_id.id,
                                'amount': receipt_line.total_paid,
                            })

                        # Account Moves Creation
                        journal_obj = self.env['account.journal'].search([('code', '=', 'NARFC')])
                        if not record.enquiry_id.partner_id:
                            stu_name = record.enquiry_id.student_full_name
                            partner_obj = self.env['res.partner'].create(
                                {'name': stu_name, 'company_type': 'person', 'company_id': self.env.user.company_id.id,
                                 'school_id': record.school_id.id})
                            record.enquiry_id.partner_id = record.partner_id = partner_obj.id
                        if self.payment_mode_id.is_cash:
                            line_ids = self._get_move_lines(record.enquiry_id.partner_id, line.name, pay_amount,
                                                            journal_obj, record.school_id)
                            account_move = self._create_move_entry(journal_obj, record.school_id, line_ids)
                            account_move.post()

                        pay_amount -= pay_amount

            pocket_payment_id = self._context.get('pocket_money_payment') or False
            if pocket_payment_id:
                pocket_payment_obj = self.env['pappaya.pocket.money'].search([('id', '=', pocket_payment_id)])
                if pocket_payment_obj:
                    pocket_payment_obj.payment_mode_id = record.payment_mode_id.id;
                    pocket_payment_obj.transaction_type = record.transaction_type.id
                    pocket_payment_obj.card_holder_name = record.card_holder_name;
                    pocket_payment_obj.card_number = record.card_number
                    pocket_payment_obj.card_type = record.card_type;
                    pocket_payment_obj.bank_machine_id = record.bank_machine_id.id
                    pocket_payment_obj.bank_machine_type_id = record.bank_machine_type_id.id;
                    pocket_payment_obj.mid_no = record.mid_no.id
                    pocket_payment_obj.tid_no = record.tid_no;
                    pocket_payment_obj.cheque_dd = record.cheque_dd;
                    pocket_payment_obj.cheque_date = record.cheque_date;
                    pocket_payment_obj.bank_name = record.bank_name.id
                    pocket_payment_obj.is_show_card_details = record.is_show_card_details;
                    pocket_payment_obj.is_show_cheque_dd_details = record.is_show_cheque_dd_details
                    pocket_payment_obj.pos_reference_no = record.pos_reference_no
                    pocket_payment_obj.pos_api_response = record.pos_api_response
                    if self._compute_pocket_payment_paid(record.fees_collection_line, self._context.get('fee_head_id')):
                        pocket_payment_obj.is_paid = True
                        pocket_payment_obj.state = status
                        for lines in record.fees_collection_line:
                            if lines.name.is_pocket_money:
                                self.enquiry_id.partner_id.write({'student_wallet_amount': (self.enquiry_id.partner_id.student_wallet_amount + self.pay_amount)})

            # ############### SMS Integration ###################
            if self.payment_mode_id.is_cash or self.payment_mode_id.is_cheque:
                self.action_send_sms()
            # ################### END ###########################
            record.payment_mode_id = record.is_show_cheque_dd_details = record.is_show_card_details = record.transaction_type = record.bank_machine_id = record.bank_machine_type_id = record.bank_name = False
            record.card_holder_name = record.card_number = record.card_type =  record.tid_no = record.cheque_dd = ''
            record.mid_no = None
            record.pos_reference_no = ''
            record.cheque_date = None
            record.pay_amount = 0.00;
            record.remarks = None;
            record.collection_date = datetime.now().date()

            form_view = self.env.ref('pappaya_fees.pappaya_fees_receipt_form')
            tree_view = self.env.ref('pappaya_fees.pappaya_fees_receipt_tree')
            if receipt_id:
                value = {
                    'domain': str([('id', '=', receipt_id.id)]),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'name': 'Fee receipt',
                    'res_model': 'pappaya.fees.receipt',
                    'view_id': False,
                    'views': [(form_view and form_view.id or False, 'form'),
                              (tree_view and tree_view.id or False, 'tree')],
                    'type': 'ir.actions.act_window',
                    'res_id': receipt_id.id,
                    'target': 'new',
                    'nodestroy': True
                }

                return value


    @api.multi
    def _compute_other_payment_paid(self, fees_collection_line, other_payment_obj):
        paid = False
        for line in fees_collection_line:
            if other_payment_obj.payment_head.id == line.name.id:
                if line.amount == line.total_paid:
                    paid = True
                    break;
        return paid

    @api.multi
    def _compute_pocket_payment_paid(self, fees_collection_line, fee_head_id):
        paid = False
        for line in fees_collection_line:
            if fee_head_id == line.name.id:
                if line.amount == line.total_paid:
                    paid = True
                    break;
        return paid

    def update_pocket_money_to_wallet(self):
        for record in self:
            for line in record.fees_collection_line:
                # Updating Student Wallet if pocket money paid directly from fee structure.
                if not record.pocket_money_id and line.name.is_pocket_money and line.term_state == 'paid':
                    self.enquiry_id.partner_id.write({'student_wallet_amount': (record.enquiry_id.partner_id.student_wallet_amount + 
                                                                                line.total_paid + line.res_adj_amt)})
                    
    @api.multi
    def _get_course_fee_line(self):
        course_fee_line = False
        for line in self.fees_collection_line:
            if line.name.is_course_fee:
                course_fee_line = line
                break;
        return course_fee_line
    
    @api.multi
    def _update_course_fee_paid_status(self):
        for record in self:
            course_fee_line = self._get_course_fee_line(); state = 'due'
            if course_fee_line:
                total_fee_paid = 0.0
                for line in record.fees_collection_line:
                    if line.name.is_course_fee_component and not line.name.is_course_fee:
                        state = line.term_state
                        total_fee_paid += (line.total_paid+line.res_adj_amt) 
                course_fee_line.total_paid = total_fee_paid
                course_fee_line.term_state = state
                
    @api.multi
    def _get_reservation_line(self):
        reservation_line = False
        for collection_line in self.fees_collection_line:
            if collection_line.name.is_reservation_fee and self.enquiry_id.sponsor_type == 'no':
                reservation_line =  collection_line
                break
        return reservation_line

    @api.multi
    def fee_pay(self):
        if self.admission_cancel:
            raise ValidationError('Sorry, The admission is cancelled..!')
        if 'other_payment' in self._context and self._context['other_payment']:
            return self.fee_pay_other_payment()
        elif 'pocket_money_payment' in self._context and self._context['pocket_money_payment']:
            return self.fee_pocket_money_payment()
        else:
            if self.enquiry_id.sponsor_type == 'yes' and self.enquiry_id.sponsor_value == 'full' and self.pay_amount < self.pay_due_total:
                raise ValidationError('Please pay actual amount as the selected sponsor type is Full')
            elif self.enquiry_id.sponsor_type == 'yes' and self.enquiry_id.sponsor_value == 'partial' and self.pay_amount < self.sponsor_amount and self.sponsor_paid == False:
                raise ValidationError('Please pay total Sponsor + Additional amount')
            receipt_obj = self.env['pappaya.fees.receipt']
            pay_amount = self.pay_amount
            res_fee = False
            for rf in self.fees_collection_line:
                if rf.name.is_reservation_fee and rf.term_state == 'due' and self.enquiry_id.sponsor_type == 'no':
                    res_fee = True
            if self.pay_amount == 0.0:
                raise ValidationError("Pay actual amount")
    
            # Pocket Money - Deposit/Transfer/Withdraw Process
            # if self.pay_amount == 0.0 or self.pay_due_total != self.pay_amount and self.pocket_money_id:
            #     raise ValidationError("Pay actual amount")
    
            fees_receipt_line_list = []
            journal_obj = self.env['account.journal'].search([('code', '=', 'NARFC')])
            reservation_line = self._get_reservation_line()
            for record in self:
                if record.enquiry_id.stage_id.sequence > 2 and not record.is_res_adjusted and reservation_line:
                    fees_receipt_line_list.append((0, 0, {
                                                    'name':reservation_line.name.id,
                                                    'amount':reservation_line.amount,
                                                    'concession_amount':reservation_line.concession_amount,
                                                    'concession_type_id':reservation_line.concession_type_id,
    #                                                           'cgst':cgst,
    #                                                           'sgst':sgst,
    #                                                           'without_gst_amt':without_gst_amt,
                                                    'total_paid':pay_amount,
                                                    'fees_coll_line_id':reservation_line.id,
                                                    'fees_coll_line_status':'paid',
                                                 }))
                    reservation_line.total_paid = reservation_line.total_paid + pay_amount
                    
                    if self.payment_mode_id.is_cash:
                        # Account Moves Creation
                        if not record.enquiry_id.partner_id and not record.enquiry_id.old_admission_no:
                            stu_name = record.enquiry_id.student_full_name
                            partner_obj = self.env['res.partner'].create({'name': stu_name,'company_type': 'person','company_id': self.env.user.company_id.id,'school_id':record.school_id.id})
                            record.enquiry_id.partner_id = record.partner_id = partner_obj.id
                        line_ids = self._get_move_lines(record.enquiry_id.partner_id, reservation_line.name, pay_amount, journal_obj, record.school_id)
                        
                        account_move = self._create_move_entry(journal_obj, record.school_id, line_ids)
                        account_move.post()
                        
                        if not self.env['pappaya.fees.receipt.line'].sudo().search([('fees_coll_line_id','=',reservation_line.id),('receipt_id.receipt_status','=','uncleared')]):
                            reservation_line.write({'term_state':'paid'})
                    else:
                        reservation_line.write({'term_state':'processing'})
                    pay_amount -=  pay_amount
                        
                else:
                    for line in record.fees_collection_line:
                        if line.pay and line.due_amount > 0.00 and pay_amount > 0.00\
                                 and not line.name.is_reservation_fee and not line.name.is_course_fee:
                            if pay_amount >= line.due_amount:
                                cgst = 0.00
                                sgst = 0.00
                                without_gst_amt = 0.00
                                cgst_percentage = (100 * line.cgst)/line.amount
                                sgst_percentage = (100 * line.sgst)/line.amount
                                cgst = (cgst_percentage * line.due_amount)/100
                                sgst = (sgst_percentage * line.due_amount)/100
                                
                                without_gst_amt =  line.due_amount - (cgst + sgst) 
                        
                                if line.name.is_course_fee_component:
                                    course_fee_line = self._get_course_fee_line()
                                    if course_fee_line:
                                        course_fee_line.total_paid = course_fee_line.total_paid + line.due_amount
                                        if course_fee_line.amount == course_fee_line.total_paid:
                                            course_fee_line.term_state = 'paid'
                                fees_receipt_line_list.append((0, 0, {
                                    'name':line.name.id,
                                    'amount':line.amount,
                                    'concession_amount':line.concession_amount,
                                    'concession_type_id':line.concession_type_id,
                                    'cgst':cgst,
                                    'sgst':sgst,
                                    'without_gst_amt':without_gst_amt,
                                    'total_paid':line.due_amount,
                                    'fees_coll_line_id':line.id,
                                    'fees_coll_line_status': 'paid',
                                 }))
                                
                                if self.payment_mode_id.is_cash: 
                                    # Account Moves Creation
                                    if not record.enquiry_id.partner_id:
                                        stu_name = record.enquiry_id.student_full_name
                                        partner_obj = self.env['res.partner'].create({'name': stu_name,'company_type': 'person','company_id': self.env.user.company_id.id,'school_id':record.school_id.id})
                                        record.enquiry_id.partner_id = record.partner_id = partner_obj.id
                                    line_ids = self._get_move_lines(record.enquiry_id.partner_id, line.name, line.due_amount, journal_obj, record.school_id)
                                    
                                    account_move = self._create_move_entry(journal_obj, record.school_id, line_ids)
                                    account_move.post()

                                    if not self.env['pappaya.fees.receipt.line'].sudo().search([('fees_coll_line_id','=',line.id),('receipt_id.receipt_status','=','uncleared')]):
                                        line.write({'term_state':'paid'})
                                    else:
                                        line.write({'term_state':'processing'})
                                    
                                    # Updating student profile
                                    if line.name.is_caution_deposit_fee:
                                        record.enquiry_id.partner_id.caution_deposit += line.due_amount

                                else:
                                    line.term_state = 'processing'
                                
                                pay_amount -=  line.due_amount
                                line.total_paid = line.total_paid + line.due_amount
                            else:
                                if record.enquiry_id.stage_id.sequence == 1 and record.enquiry_id.sponsor_type == 'no':
                                    raise ValidationError("Sale of application amount cannot be paid by partial"+'\n\n'+ \
                                                          'Please pay'+ '-- RS '+str(line.amount)+' to proceed.'
                                                          )
                                
                                cgst = 0.00
                                sgst = 0.00
                                without_gst_amt = 0.00
                                cgst_percentage = (100 * line.cgst)/line.amount
                                sgst_percentage = (100 * line.sgst)/line.amount
                                cgst = (cgst_percentage * pay_amount)/100
                                sgst = (sgst_percentage * pay_amount)/100
                                
                                without_gst_amt =  pay_amount - (cgst + sgst)
                                if line.name.is_course_fee_component:
                                    course_fee_line = self._get_course_fee_line()
                                    if course_fee_line:
                                        course_fee_line.total_paid = course_fee_line.total_paid + pay_amount
    #                                     if self.payment_mode_id.is_cheque or self.payment_mode_id.is_card:
    #                                         course_fee_line.term_state = 'processing'
    #                                     else:
                                        course_fee_line.term_state = 'due'
                                fees_receipt_line_list.append((0, 0, {
                                                                'name':line.name.id,
                                                                'amount':line.amount,
                                                                'concession_amount':line.concession_amount,
                                                                'concession_type_id':line.concession_type_id,
                                                                'cgst':cgst,
                                                                'sgst':sgst,
                                                                'without_gst_amt':without_gst_amt,
                                                                'total_paid':pay_amount,
                                                                'fees_coll_line_id': line.id,
                                                                'fees_coll_line_status': 'due',
                                                             }))
                                line.total_paid = line.total_paid + pay_amount
                                
                                
                                # Account Moves Creation
                                if self.payment_mode_id.is_cash: 
                                    # Partner
                                    if not record.enquiry_id.partner_id:
                                        stu_name = record.enquiry_id.name + '/' + str(record.enquiry_id.id)
                                        partner_obj = self.env['res.partner'].create({'name': stu_name,'company_type': 'person','company_id': self.env.user.company_id.id,'school_id':record.school_id.id})
                                        record.enquiry_id.partner_id = record.partner_id = partner_obj.id
                                    # Journal
                                    journal_obj = self.env['account.journal'].search([('code','=','NARFC')])
                                    # Receivable Account
                                    # account_obj = self.env['account.account'].search([('name','=','Narayana Fee Collection Receivable')])
                                    line_ids = self._get_move_lines(record.enquiry_id.partner_id, line.name, pay_amount, journal_obj, record.school_id)
                                    account_move = self._create_move_entry(journal_obj, record.school_id, line_ids)
                                    account_move.post()
                                    
                                    # Updating student profile
                                    if line.name.is_caution_deposit_fee:
                                        record.enquiry_id.partner_id.caution_deposit += pay_amount
                                         
                                else:
                                    line.term_state = 'processing'
                                
                                pay_amount -=  pay_amount
                        # Updating Student Wallet if pocket money paid directly from fee structure.
                        # if not self.pocket_money_id and line.name.is_pocket_money:
                        #     if self.payment_mode_id.is_cash:
                        #         self.enquiry_id.partner_id.write({'student_wallet_amount': (record.enquiry_id.partner_id.student_wallet_amount + line.total_paid)})
                                
                        # Reservation fee
                        if line.pay and line.term_state == 'due' and pay_amount > 0.00 \
                                and line.name.is_reservation_fee and record.enquiry_id.sponsor_type == 'no':
                            if line.amount > pay_amount:
                                # Amount will be moved to parking account
                                total_amount = 0.0
                                for fee_line in record.fees_collection_line:
                                    if fee_line.name.is_soa_fee:
                                        total_amount += fee_line.amount
                                        break
                                message = 'Reservation fee cannot be paid partially.'
                                if record.enquiry_id.stage_id.sequence == 1:
                                    message = 'You should pay'+'\n\n'+ \
                                                'Sale of Application' + '   --   Rs. ' + str(total_amount) + ' Or else \n' +\
                                                'Sale of Application' +' and '+line.name.name+'   --   Minimum Rs. '+str(total_amount+line.amount)
                                else:
                                    message = line.name.name+' Cannot be paid partially.'+'\n\n'+'You should pay'+ '   --  Minimum Rs. ' + str(line.amount) + ' to proceed.'
                                raise ValidationError(_(message))
                            else:
                                fees_receipt_line_list.append((0, 0, {
                                                                'name':line.name.id,
                                                                'amount':line.amount,
                                                                'concession_amount':line.concession_amount,
                                                                'concession_type_id':line.concession_type_id,
            #                                                           'cgst':cgst,
            #                                                           'sgst':sgst,
            #                                                           'without_gst_amt':without_gst_amt,
                                                                'total_paid':pay_amount,
                                                                'fees_coll_line_id':line.id,
                                                                'fees_coll_line_status':'paid',
                                                             }))
                                line.total_paid = line.total_paid + pay_amount
                                if self.payment_mode_id.is_cash:

                                    if not self.env['pappaya.fees.receipt.line'].sudo().search([('fees_coll_line_id','=',line.id),('receipt_id.receipt_status','=','uncleared')]):
                                        line.write({'term_state':'paid'})
                                    else:
                                        line.write({'term_state':'processing'})
                                    
                                    # Account Moves Creation
                                    if not record.enquiry_id.partner_id:
                                        stu_name = record.enquiry_id.student_full_name
                                        partner_obj = self.env['res.partner'].create({'name': stu_name,'company_type': 'person','company_id': self.env.user.company_id.id,'school_id':record.school_id.id})
                                        record.enquiry_id.partner_id = record.partner_id = partner_obj.id
                                    line_ids = self._get_move_lines(record.enquiry_id.partner_id, line.name, pay_amount, journal_obj, record.school_id)
                                    
                                    account_move = self._create_move_entry(journal_obj, record.school_id, line_ids)
                                    account_move.post()
                                                                        
                                else:
                                    line.term_state = 'processing'

                                pay_amount -=  pay_amount    
            
            # Update course Fee Paid
            self._update_course_fee_paid_status()
                    
            """ Handle Excess amount (To be moved to caution deposit)"""
            is_caution_deposit_fee_adjusted = False
            if pay_amount > 0.0:
                for fee_line in self.fees_collection_line:
                    if fee_line.name.is_caution_deposit_fee:
                        fee_line.total_paid += pay_amount
                        fees_receipt_line_list.append((0, 0, {
                                                        'name':fee_line.name.id,
                                                        'amount':fee_line.amount,
                                                        'concession_amount':fee_line.concession_amount,
                                                        'concession_type_id':fee_line.concession_type_id,
                                                        'cgst':fee_line.cgst,
                                                        'sgst':fee_line.sgst,
                                                        'without_gst_amt':fee_line.amount,
                                                        'total_paid':pay_amount,
                                                        'fees_coll_line_id': fee_line.id,
                                                        'fees_coll_line_status': 'paid',
                                                     }))
                        is_caution_deposit_fee_adjusted = True
                        
                        if self.payment_mode_id.is_cash:
                            # Account Moves Creation
                            if not record.enquiry_id.partner_id:
                                stu_name = record.enquiry_id.student_full_name
                                partner_obj = self.env['res.partner'].create({'name': stu_name,'company_type': 'person','company_id': self.env.user.company_id.id,'school_id':record.school_id.id})
                                record.enquiry_id.partner_id = record.partner_id = partner_obj.id
                            line_ids = self._get_move_lines(record.enquiry_id.partner_id, fee_line.name, fee_line.due_amount, journal_obj, record.school_id)
                            account_move = self._create_move_entry(journal_obj, record.school_id, line_ids)
                            account_move.post()   
                            # Updating student profile    
                            record.enquiry_id.partner_id.caution_deposit += pay_amount
                                              
                            if not self.env['pappaya.fees.receipt.line'].sudo().search([('fees_coll_line_id','=',fee_line.id),('receipt_id.receipt_status','=','uncleared')]):
                                fee_line.write({'term_state':'paid'})
                            else:
                                fee_line.write({'term_state':'processing'})
                        else:
                            fee_line.write({'term_state':'processing'})   
                        pay_amount = 0.0

                if not is_caution_deposit_fee_adjusted:
                    raise ValidationError("Pay actual amount!")

            if self.payment_mode_id.is_cash:
                receipt_status = 'cleared'
            else:
                receipt_status = 'uncleared'
                        
            receipt = receipt_obj.sudo().create({
                                             'state':'paid',
                                             'fee_collection_id':record.id,
                                             'school_id' : record.school_id.id,
                                             'academic_year_id' : record.academic_year_id.id,
                                             'enquiry_id':record.enquiry_id.id,
                                             'payment_mode_id': record.payment_mode_id.id,
                                             'transaction_type': record.transaction_type.id,
                                             'is_show_card_details':record.is_show_card_details,
                                             'is_show_cheque_dd_details': record.is_show_cheque_dd_details,
                                             'bank_machine_id': record.bank_machine_id.id,
                                             'bank_machine_type_id':record.bank_machine_type_id.id,
                                             'card_holder_name': record.card_holder_name,
                                             'card_number': record.card_number,
                                             'card_type': record.card_type,
                                             'mid_no': record.mid_no.id,
                                             'tid_no': record.tid_no,
                                             'cheque_dd' : record.cheque_dd,
                                             'cheque_date' : record.cheque_date,
                                             'bank_name':record.bank_name.id,
                                             'remarks':record.remarks,
                                             'receipt_date':record.collection_date,
                                             'fees_receipt_line':fees_receipt_line_list,
                                             'receipt_status':receipt_status,
                                             'pos_reference_no': record.pos_reference_no,
                                             'pos_api_response': record.pos_api_response
                                           })
            receipt.write({'virtual_acc_no':self.enquiry_id.virtual_acc_no, 'ifsc_code':'KKBK0000552'})
            if self.bank_chellan_id and self.payment_mode_id.is_challan:
                receipt.write({
                    'ibank_transaction_id':self.bank_chellan_id.ibank_transaction_id if self.bank_chellan_id.ibank_transaction_id else '',
                    'instrument_no':self.bank_chellan_id.instrument_no if self.bank_chellan_id.instrument_no else '',
                    'instrument_date':self.bank_chellan_id.instrument_date if self.bank_chellan_id.instrument_date else '',
                    'pay_mode':self.bank_chellan_id.pay_mode,
                    'transaction_date':self.bank_chellan_id.transaction_date,
                    'isure_id':self.bank_chellan_id.isure_id,
                    'micr_code':self.bank_chellan_id.micr_code if self.bank_chellan_id.micr_code else '',
                    'bank_name_char':self.bank_chellan_id.bank_name if self.bank_chellan_id.bank_name else '',
                    'branch_name':self.bank_chellan_id.branch_name if self.bank_chellan_id.branch_name else '',
                    'client_code':self.bank_chellan_id.client_code,
                    })
            if self.paytm_order_ref:
                receipt.write({'paytm_order_ref':self.paytm_order_ref})
            
            fee_receipt_ledger_line = []
            for frl in receipt.fees_receipt_line:
                fee_receipt_ledger_line.append((0, 0, {
                                                    'fees_receipt_id': receipt.id,
                                                    'name':receipt.receipt_no,
                                                    'posting_date':receipt.receipt_date,
                                                    'fees_head':frl.name.name,
                                                    'transaction':receipt.remarks,
                                                    'concession_amount':frl.concession_amount,
                                                    'payment_mode_id':receipt.payment_mode_id.id,
                                                    'amount':frl.total_paid,
                                                    }))

#             if receipt and line.name.is_caution_deposit_fee == True and record.payment_mode_id.is_cash == True:
#                 self.enquiry_id.partner_id.caution_deposit += line.total_paid

            ledger_obj = self.env['pappaya.fees.ledger']
            led_obj_ref = ledger_obj.search([('fee_collection_id', '=', record.id)])
            if led_obj_ref:
                led_obj_ref.fee_receipt_ledger_line = fee_receipt_ledger_line
            if self.payment_mode_id.is_cash: 

                fee_ledger_line = []

                for rec1 in self.fees_collection_line:
                    fee_ledger_line.append((0, 0, {
                                                    'fee_line_id':rec1.id,
                                                    'name':rec1.name.name,
                                                    'credit':rec1.amount,
                                                    'concession_amount':rec1.concession_amount,
                                                    'concession_type_id':rec1.concession_type_id.id,
                                                    'debit':rec1.total_paid,
                                                    'balance':rec1.amount - (rec1.total_paid + rec1.concession_amount),
                                                    }))
                if not led_obj_ref:
                    led_obj_ref = ledger_obj.sudo().create({
                        'admission_number': record.admission_number,
                        'enquiry_id': record.enquiry_id.id,
                        'fee_collection_id':record.id,
                        'school_id' : record.school_id.id,
                        'academic_year_id' : record.academic_year_id.id,
                        'course_id': record.enquiry_id.course_id.id,
                        'group_id': record.enquiry_id.group_id.id,
                        'batch_id': record.enquiry_id.batch_id.id,
                        'package': record.enquiry_id.package.id,
                        'package_id': record.enquiry_id.package_id.id,
                        'fee_ledger_line':fee_ledger_line,
                        'fee_receipt_ledger_line':fee_receipt_ledger_line,
                                })
                else:
                    for receipt_line in receipt.fees_receipt_line:
                        for line in led_obj_ref.fee_ledger_line:
                            if receipt_line.name.name == line.name :
                                line.debit += receipt_line.total_paid
                                line.balance -= receipt_line.total_paid
            else:
                if not led_obj_ref:
                    fee_ledger_line = []
                    for rec1 in self.fees_collection_line:
                        fee_ledger_line.append((0, 0, {
                                                        'fee_line_id':rec1.id,
                                                        'name':rec1.name.name,
                                                        'credit':rec1.amount,
                                                        'concession_amount':rec1.concession_amount,
                                                        'concession_type_id':rec1.concession_type_id.id,
                                                        'debit':0.00,
                                                        'balance':rec1.amount,
                                                        }))
                    if not led_obj_ref:
                        led_obj_ref = ledger_obj.sudo().create({
                                                            'admission_number': record.admission_number,
                                                            'enquiry_id': record.enquiry_id.id,
                                                            'fee_collection_id':record.id,
                                                            'school_id' : record.school_id.id,
                                                            'academic_year_id' : record.academic_year_id.id,
                                                            'course_id': record.enquiry_id.course_id.id,
                                                            'group_id': record.enquiry_id.group_id.id,
                                                            'batch_id': record.enquiry_id.batch_id.id,
                                                            'package': record.enquiry_id.package.id,
                                                            'package_id': record.enquiry_id.package_id.id,
                                                            'fee_ledger_line':fee_ledger_line,
                                                            'fee_receipt_ledger_line':fee_receipt_ledger_line
                                                            })
                course_fee_ledger_line = self.env['pappaya.fees.ledger.line'].sudo().search([('fees_ledger_id','=',led_obj_ref.id),
                                                                                            ('fee_line_id.name.is_course_fee','=',True)])
                if course_fee_ledger_line:
                    course_fee_ledger_line.write({'debit':0.0,'balance':0.0})
                    for ledger_line in led_obj_ref.fee_ledger_line:
                        if ledger_line.fee_line_id.name.is_course_fee_component and not ledger_line.fee_line_id.name.is_course_fee:
                            course_fee_ledger_line.debit += ledger_line.debit
                            course_fee_ledger_line.balance += ledger_line.balance
                        
            """Update Admission Status"""
            
            self.update_admission_stage_to_soa()
            self.update_admission_stage_to_reservation()
            self.update_admission_stage_to_admission() 
            self.action_generate_no()
            
            if self.payment_mode_id.is_cash or self.payment_mode_id.is_cheque:
                self.action_send_sms()
            record.payment_mode_id = record.is_show_card_details = record.is_show_cheque_dd_details = record.transaction_type = record.bank_machine_id = record.bank_machine_type_id = record.bank_name = False
            record.card_holder_name = record.card_number = record.card_type =  record.tid_no = record.cheque_dd = ''
            record.mid_no = None
            record.pos_reference_no = ''
            record.cheque_date = None
            record.pay_amount = 0.00;record.remarks = None;record.collection_date = datetime.now().date()
            self.is_amt = False

            template_id = self.env.ref('pappaya_fees.email_template_fee_details')
            template_id.send_mail(self.id)
            form_view = self.env.ref('pappaya_fees.pappaya_fees_receipt_form')
            tree_view = self.env.ref('pappaya_fees.pappaya_fees_receipt_tree')
            value = {
                'domain': str([('id', '=', receipt.id)]),
                'view_type': 'form',
                'view_mode': 'form',
                'name':'Fee receipt',
                'res_model': 'pappaya.fees.receipt',
                'view_id': False,
                'views': [(form_view and form_view.id or False, 'form'),
                           (tree_view and tree_view.id or False, 'tree')],
                'type': 'ir.actions.act_window',
                'res_id': receipt.id,
                'target': 'new',
                'nodestroy': True,
                'context':{'receipt_no':receipt.receipt_no}
             }
            return value

    @api.multi
    def action_generate_no(self):
        for record in self:
            if record.enquiry_id:
                # Application/Reservation/Admission no generation
                if record.enquiry_id.stage_id.sequence > 1 and not record.enquiry_id.application_no:
                        sequence = self.env['pappaya.admission'].sudo().search_count([('stage_id.sequence', '>', 1)])
                        record.enquiry_id.write({'application_no': ("{0:07d}".format(sequence + 1))})
                
                if not record.enquiry_id.res_no and record.enquiry_id.stage_id.sequence > 2 and record.enquiry_id.old_new == 'new' and record.enquiry_id.branch_id.office_type_id.type == 'school':
                    sequence = self.env['pappaya.admission'].sudo().search_count([('stage_id.sequence', '>', 2), ('office_type_id.type', '=', 'school')])
                    record.enquiry_id.write({'res_no': '56' + str("{0:05d}".format(sequence + 1)), 'admission_no': '56' + str("{0:05d}".format(sequence + 1)), 'is_res_stage': True})
                    
                elif not record.enquiry_id.res_no and record.enquiry_id.stage_id.sequence > 2 and record.enquiry_id.old_new == 'new' and record.enquiry_id.branch_id.office_type_id.type != 'school':
                    sequence = self.env['pappaya.admission'].sudo().search_count([('stage_id.sequence', '>', 2), ('office_type_id.type', '!=', 'school')])
                    record.enquiry_id.write({'res_no': '18' + str("{0:05d}".format(sequence + 1)), 'admission_no': '18' + str("{0:05d}".format(sequence + 1)), 'is_res_stage': True})

                """ Virtual Account Codification """
                if record.enquiry_id.stage_id.sequence >= 3:
                    entity = record.enquiry_id.branch_id.parent_id
                    if entity:
                        record.enquiry_id.write({'virtual_acc_no':'NEG'+ str(entity.code+record.enquiry_id.res_no)})
                
                # Creating Student Profile
                if record.enquiry_id.stage_id.sequence > 2 and record.enquiry_id.old_new == 'new':
                    record.enquiry_id.existing_old_student()
                    record.enquiry_id.is_student_created = True

                # Updating Admission number
                if record.enquiry_id.res_no and record.enquiry_id.stage_id.sequence > 3:
                    record.enquiry_id.is_adm_stage = True
                    record.enquiry_id.is_res_stage = False
                    record.enquiry_id.is_final_stage = True

                # Updating Caution Deposit and pocket money in Student Profile
                if record.enquiry_id.partner_id:
                    for fee in record.enquiry_id.fees_collection_o2m_id:                        
                        if fee.name.is_pocket_money and fee.term_state == 'paid':
                            record.enquiry_id.partner_id.student_wallet_amount = (fee.amount)
                        elif fee.name.is_pocket_money and fee.term_state == 'due' and fee.res_adj_amt > 0.0:
                            record.enquiry_id.partner_id.student_wallet_amount += (fee.res_adj_amt)

                # Grade Joining Document
                for i in record.enquiry_id.enq_grade_doc_o2m:
                    if i.required and not i.document_file:
                        raise ValidationError(_('Required %s Document not attached') % i.document_name)
                grade_doc_obj = self.env['pappaya.enq.grade_doc']
                docs_exists = grade_doc_obj.search([('stage_name', '=', record.enquiry_id.stage_id.name),
                                                    ('enquiry_id', '=', record.enquiry_id.id)])
                if record.enquiry_id.stage_id.grade_join_doc_o2m and not docs_exists:
                    for i in record.enquiry_id.stage_id.grade_join_doc_o2m:
                        grade_doc_obj.create({'document_name': i.document_name,
                                              'wrk_grade_id': i.id,
                                              'required': i.required,
                                              'stage_name': record.enquiry_id.stage_id.name,
                                              'enquiry_id': record.enquiry_id.id})

                # Tracking History
                cont = record.enquiry_id.pre_stage_id.name if record.enquiry_id.pre_stage_id.name else 'Start'
                mov_cont = cont + '->' + record.enquiry_id.stage_id.name
                hist_obj = self.env['pappaya.enq.workflow.history']
                amt, hist_amt = 0.0, 0.0
                for stud_fee in record.enquiry_id.fees_collection_o2m_id:
                    if not stud_fee.name.is_course_fee_component and stud_fee.term_state in ['paid','processing']:
                        amt += stud_fee.total_paid
                for hist in record.enquiry_id.enquiry_histroy_o2m:
                    hist_amt += hist.amount
                value = {'document_number': record.enquiry_id.form_no or '',
                         'movement_stage': mov_cont,
                         'user_id': self.env.uid,
                         'updated_on': datetime.today(),
                         'description': (str(record.enquiry_id.branch_id.name) + ' -> ' +str(record.enquiry_id.branch_id_at.name)),
                         'enquiry_id': record.enquiry_id.id,
                         'course_id': record.enquiry_id.course_id.id,
                         'group_id': record.enquiry_id.group_id.id,
                         'batch_id': record.enquiry_id.batch_id.id,
                         'package_id': record.enquiry_id.package.id,
                         'course_package_id': record.enquiry_id.package_id.id,
                         'medium_id': record.enquiry_id.medium_id.id,
                         'amount': (amt - hist_amt)
                         }
                hist_obj.create(value)
                self.sponsor_to_admission()

    @api.multi
    def sponsor_to_admission(self):
        for rec in self:
            if rec.enquiry_id.sponsor_type == 'yes' and rec.enquiry_id.sponsor_value == 'partial':
                stage_obj = self.env['pappaya.business.stage'].search([('is_final_stage','=', True), ('school_id','=',self.enquiry_id.branch_id.id)])
                rec.sponsor_paid = True
                rec.enquiry_id.write({'stage_id': stage_obj.id, 'sponsor_paid': True})

    @api.multi
    def update_admission_stage_to_soa(self):
        for record in self:
            if record.enquiry_id:
                if record.enquiry_id.stage_id.sequence == 1:
                    record.enquiry_id.write({'pre_stage_id' : record.enquiry_id.stage_id.id,'is_soa_stage':True})
                    paid = True
                    for line in record.fees_collection_line:
                        if line.id in record.enquiry_id.stage_id.fees_id.ids:
                            if line.term_state == 'due':
                                paid = False
                    if paid:
                        next_stage = self.env['pappaya.business.stage'].search([('sequence','=',record.enquiry_id.stage_id.sequence+1),
                                                                                ('school_id','=',record.enquiry_id.branch_id.id)], limit=1)
                        record.enquiry_id.stage_id = next_stage.id
        return True
                                 
    @api.multi
    def update_admission_stage_to_reservation(self):
        for record in self: 
            if record.enquiry_id:
                if record.enquiry_id.stage_id.sequence == 2:
                    if record.enquiry_id.pre_stage_id.name != record.enquiry_id.stage_id.name:
                        record.enquiry_id.write({'pre_stage_id' : record.enquiry_id.stage_id.id})
                    reservation_line = False
                    for fee_line in record.fees_collection_line:
                        if fee_line.name.is_reservation_fee:
                            reservation_line = fee_line 
                            break
                    if reservation_line.amount <= reservation_line.total_paid:
                        next_stage = self.env['pappaya.business.stage'].search([('sequence','=',record.enquiry_id.stage_id.sequence+1),
                                                                                ('school_id','=',record.enquiry_id.branch_id.id)], limit=1)
                        record.enquiry_id.stage_id = next_stage.id
        return True
         
    @api.multi
    def update_admission_stage_to_admission(self):
        for record in self: 
            if record.enquiry_id:
                reservation_line = self._get_reservation_line()

                mandatory_fees, minimum_admission_fee = record.enquiry_id._get_minimum_admisison_mandatory_fees()
                total_fees_required = mandatory_fees + minimum_admission_fee
                total_reservatoin_paid = 0.0
                for fee_line in record.fees_collection_line:
                    if fee_line.name.is_reservation_fee or fee_line.name.is_course_fee_component and not fee_line.name.is_course_fee and record.enquiry_id.sponsor_type == 'no':
                        total_reservatoin_paid += fee_line.total_paid + fee_line.res_adj_amt
                if total_reservatoin_paid >= total_fees_required:
                    if reservation_line and reservation_line.term_state == 'paid':
                        if not self.is_res_adjusted:
                            record.enquiry_id.adjust_reservation_fees()
                            record._update_course_fee_paid_status()
                    
                    if record.enquiry_id.stage_id.sequence == 3:
                        if record.enquiry_id.pre_stage_id.name != record.enquiry_id.stage_id.name:
                            record.enquiry_id.write({'pre_stage_id' : record.enquiry_id.stage_id.id})                            
                        next_stage = self.env['pappaya.business.stage'].search([('sequence','=',record.enquiry_id.stage_id.sequence+1),
                                                                        ('school_id','=',record.enquiry_id.branch_id.id)], limit=1)
                        record.enquiry_id.stage_id = next_stage.id
        return True
    
    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")

    @api.multi
    def _create_acc_journal_entries(self, student_obj, fee_head_obj, amount_paid, journal_obj, collection_id, deposit_bank):
        move_lines = []
        operating_unit_obj = collection_id.school_id
        if not operating_unit_obj.credit_account_id or not operating_unit_obj.parent_id.co_debit_account_id:
            raise ValidationError('Please configure Dr/Cr account in Branch/Entity')
        move_lines.append((0, 0, {
            'name': fee_head_obj.name,  # a label so accountant can understand where this line come from
            'debit': 0,
            'credit': amount_paid,
            'account_id': fee_head_obj.credit_account_id.id,  # Course Fee chart of account.
            'date': str(datetime.today().date()),
            'partner_id': student_obj.id,
            'journal_id': journal_obj.id,  # Cash journal
            'company_id': journal_obj.company_id.id,
            'currency_id': journal_obj.company_id.currency_id.id,
            'date_maturity': str(datetime.today().date()),
            'operating_unit_id': operating_unit_obj.id,
            'fees_collection_id': collection_id.id,
        }))

        move_lines.append((0, 0, {
            'name': operating_unit_obj.parent_id.co_debit_account_id.name,
            'debit': amount_paid,
            'credit': 0,
            # 'account_id': student_obj.property_account_receivable_id.id,# Student account
            # ~ 'account_id': fee_head_obj.contra_account_id.id,# Contra Ledger
            'account_id': operating_unit_obj.parent_id.co_debit_account_id.id,  # Contra Ledger
            'date': str(datetime.today().date()),
            'partner_id': student_obj.id,
            'journal_id': journal_obj.id,
            'company_id': journal_obj.company_id.id,
            'currency_id': journal_obj.company_id.currency_id.id,  # currency id of narayana
            'date_maturity': str(datetime.today().date()),
            'operating_unit_id': operating_unit_obj.parent_id.id,
            'fees_collection_id': collection_id.id,
        }))

        account_move_obj = self.env['account.move'].create({
            'journal_id': journal_obj.id,  # journal ex: sale journal, cash journal, bank journal....
            'date': str(datetime.today().date()),
            'state': 'draft',
            'company_id': journal_obj.company_id.id,
            'operating_unit_id': operating_unit_obj.id,
            'line_ids': move_lines,  # this is one2many field to account.move.line
            'fees_collection_id': collection_id.id,
        })
        account_move_obj.post()
        move_lines1 = []

        move_lines1.append((0, 0, {
            'name': operating_unit_obj.credit_account_id.name,
            # a label so accountant can understand where this line come from
            'debit': 0,
            'credit': amount_paid,
            'account_id': operating_unit_obj.credit_account_id.id,  # Course Fee chart of account.
            'date': str(datetime.today().date()),
            'partner_id': student_obj.id,
            'journal_id': journal_obj.id,  # Cash journal
            'company_id': journal_obj.company_id.id,
            'currency_id': journal_obj.company_id.currency_id.id,
            'date_maturity': str(datetime.today().date()),
            'operating_unit_id': operating_unit_obj.id,
            'fees_collection_id': collection_id.id,
        }))
        if not deposit_bank.debit_account_id:
            raise ValidationError('Please configure debit account in bank mapping')
        bank_ac = deposit_bank.debit_account_id
        move_lines1.append((0, 0, {
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
            'operating_unit_id': operating_unit_obj.parent_id.id,
            'fees_collection_id': collection_id.id,
            'bank_id': deposit_bank.id
        }))
        account_move_obj1 = self.env['account.move'].create({
            'journal_id': journal_obj.id,  # journal ex: sale journal, cash journal, bank journal....
            'date': str(datetime.today().date()),
            'state': 'draft',
            'company_id': journal_obj.company_id.id,
            'operating_unit_id': operating_unit_obj.parent_id.id,
            'line_ids': move_lines1,  # this is one2many field to account.move.line
            'fees_collection_id': collection_id.id,
        })
        account_move_obj1.post()
        return True

class StudentFeesCollectionLine(models.Model):
    _name = 'student.fees.collection'
    
    pay = fields.Boolean('Pay', default=True)
    name = fields.Many2one('pappaya.fees.head','Fee Type')
    concession_type_id = fields.Many2one('pappaya.concession.reason', 'Concession Reason')
    partial_payment = fields.Boolean('Partial Payment')
    amount = fields.Float('Total Amount')
    concession_amount = fields.Float('Concession')
    concession_applied = fields.Boolean('Concession Applied')
    due_amount = fields.Float('Due Amount', compute='calculate_due', store=True)
    fine_amount = fields.Float('Fine Amount')
    total_paid = fields.Float('Total Paid')
    term_state = fields.Selection([('due', 'Due'),('open','Open'),('paid', 'Paid'),('processing','Processing'),('transfer','Transfer')], 'Status')
    collection_id = fields.Many2one('pappaya.fees.collection', 'Collection')
    res_adj_amt = fields.Float('Reservation Adjustment')
    res_adj_amt_extra = fields.Float('Excess Amount')
    refund_amount = fields.Float('Refund Amount')
    allow_refund = fields.Boolean('Allow Refund', compute='check_refund')
    is_refunded = fields.Boolean('Refunded', default=False)
    cgst = fields.Float('CGST')
    sgst = fields.Float('SGST')
    gst_total = fields.Float('Unit Price') # NOTE: gst_total is unit price
    # Transport Installment related fields
    is_transport = fields.Boolean(related='name.is_transport_fee', string='Is Transport?', store=True)
    transport_installment_line = fields.One2many('transport.fees.collection', 'stud_collection_id',string='Transport Installment Fees')
    payment_mode_id = fields.Many2one('pappaya.paymode', 'Payment Mode')
    transaction_type = fields.Many2one('pappaya.master', 'Transaction Type')
    is_show_card_details = fields.Boolean('Show Card Details')
    is_show_cheque_dd_details = fields.Boolean('Is Show Cheque Details')
    is_show_cash_details = fields.Boolean('Is Show Cash Details')
    card_holder_name = fields.Char('Card Holder Name')
    card_number = fields.Char('Card Number')
    card_type = fields.Char('Card Type')
    # card_type = fields.Many2one('pappaya.master', 'Card Type')
    bank_machine_id = fields.Many2one('bank.machine', 'Bank Machine')
    bank_machine_type_id = fields.Many2one('pappaya.master', 'Bank Machine Type',related='bank_machine_id.bank_machine_type_id')
    mid_no = fields.Char('M.I.D.No(last 6 digits)')
    tid_no = fields.Char('T.I.D.No')
    cheque_dd = fields.Char('Cheque/DD No', size=30)
    bank_name = fields.Many2one('res.bank', 'Bank Name')
    pay_amount = fields.Float(string='Pay Amount')
    is_update = fields.Boolean(string='Is Update?', default=False)
    other_payment_id = fields.Many2one('pappaya.other.payment', 'Other Payment')
    req_refund_amount = fields.Float('Req. Refund Amount')
    cheque_date = fields.Date('Cheque Date')
    less_sequence = fields.Integer('Less\nSequecne')
    tax_ids = fields.Many2many(comodel_name='account.tax', string='Taxes')
    
    # @api.onchange('cheque_date')
    # def onchange_cheque_date(self):
    #     cheque_date = datetime.strptime(self.cheque_date, "%Y-%m-%d").date()
    #     if cheque_date < date.today():
    #         raise ValidationError('Please enter valid Cheque Date..!')

    @api.onchange('payment_mode_id')
    def onchange_payment_mode_id(self):
        self.is_show_card_details = True if self.payment_mode_id.is_card else False
        self.is_show_cheque_dd_details = True if self.payment_mode_id.is_cheque else False
        self.is_show_cash_details = True if self.payment_mode_id.is_cash else False

    @api.onchange('cheque_dd')
    def onchange_cheque_dd(self):
        for rec in self:
            if rec.cheque_dd:
                cheque_dd = re.match('^[\d]*$', rec.cheque_dd)
                if not cheque_dd:
                    raise ValidationError(_("Please enter a valid Cheque/DD Number"))

    @api.multi
    @api.depends('term_state')
    def check_refund(self): 
        for rec in self:
            if rec.term_state == 'paid' and rec.name.is_refundable_fee:
                rec.allow_refund = True
    
    @api.onchange('refund_amount')
    def _onchange_refund_amount(self):
        if self.refund_amount:
            total_paid = self.res_adj_amt + self.total_paid
            if self.refund_amount > total_paid:
                raise ValidationError("Refund amount should not be greater than total amount.")
            
    @api.multi
    @api.depends('amount', 'res_adj_amt', 'total_paid', 'res_adj_amt_extra', 'concession_amount', 'fine_amount')
    def calculate_due(self): 
        for line in self:
            due_amount = line.amount - line.total_paid - line.res_adj_amt - line.fine_amount - line.adjusted_amount
            if due_amount > 0:
                line.due_amount = due_amount - line.concession_amount
            else:
                line.due_amount = 0.0

    @api.multi
    def update_transport_installment(self):
        for rec in self:
            if self.is_transport:
                install_ids = []
                if self.due_amount == 0:
                    raise ValidationError('Sorry, Due Amount should be greater than zero..!')
                count = len(rec.collection_id.school_id.transport_installment_ids.ids)
                if count > 0:
                    due = (self.due_amount / count) if self.due_amount else 0
                    if rec.collection_id.school_id.transport_installment_ids:
                        for installment in rec.collection_id.school_id.transport_installment_ids:
                            install_ids.append((0, 0, {
                                'due_date': installment.due_date,
                                'amount': due,
                                'fine_amount': 0.0,
                                'total_paid': 0.0,
                                'term_state': 'due',
                                'stud_collection_id': self.id,
                            }))
                        self.transport_installment_line = install_ids
                        self.is_update = True
                else:
                    raise ValidationError("Please configure transport installments in branch!")

    @api.multi
    def create_receipt(self):
        fees_receipt_line_list = []
        for line in self:
            fees_receipt_line_list.append((0, 0, {
                                            'name': line.name.id,
                                            'amount': line.amount,
                                            'concession_amount': line.concession_amount,
                                            'total_paid': self.total_paid,
                                            }))
        self.env['pappaya.fees.receipt'].create({
                                            'state': 'paid',
                                            'fee_collection_id': self.collection_id.id,
                                            'school_id': self.collection_id.school_id.id,
                                            'academic_year_id': self.collection_id.academic_year_id.id,
                                            'enquiry_id': self.collection_id.enquiry_id.id,
                                            'payment_mode_id': self.payment_mode_id.id,
                                            'transaction_type': self.transaction_type.id,
                                            'is_show_card_details': self.is_show_card_details,
                                            'is_show_cheque_dd_details': self.is_show_cheque_dd_details,
                                            'bank_machine_id': self.bank_machine_id.id,
                                            'bank_machine_type_id': self.bank_machine_type_id.id,
                                            'card_holder_name': self.card_holder_name,
                                            'card_number': self.card_number,
                                            'card_type': self.card_type,
                                            'mid_no': self.mid_no,
                                            'tid_no': self.tid_no,
                                            'cheque_dd': self.cheque_dd,
                                            'cheque_date': self.cheque_date,
                                            'bank_name': self.bank_name.id,
                                            'remarks': self.collection_id.remarks,
                                            'receipt_date': datetime.today().date(),
                                            'fees_receipt_line': fees_receipt_line_list,
                                        })

    @api.multi
    def update_ledger(self):
        for ledger in self.env['pappaya.fees.ledger'].search([('enquiry_id','=',self.collection_id.enquiry_id.id),('admission_number','=',self.collection_id.admission_number),
                                                              ('school_id','=',self.collection_id.school_id.id),('academic_year_id','=',self.collection_id.academic_year_id.id)]):
            for line in ledger.fee_ledger_line:
                if line.name in self.name.name:
                    line.debit = self.pay_amount + line.debit

    @api.multi
    def pay_installment(self):
        pay_amount = self.pay_amount
        transport_obj = self.env['transport.fees.collection'].search([('stud_collection_id', '=', self.id),('term_state', '=', 'due'),
                                                                      ('due_date', '<', str(datetime.today().date()))])
        amount = sum([t.amount + t.fine_amount for t in self.transport_installment_line])
        fine_amount = sum([t.fine_amount for t in self.transport_installment_line])
        if  pay_amount > 0.0 and pay_amount > self.due_amount:
            raise ValidationError("Pay actual amount")
        total_paid = 0.0
        status = 'paid' if self.payment_mode_id.is_cash else 'processing'
        for transport_line in self.transport_installment_line:
            if transport_line.term_state=='due' and pay_amount >= transport_line.total_amount:
                transport_line.write({
                    'total_paid': transport_line.total_amount,
                    'paid_date': str(datetime.today().date()),
                    'term_state': status, 
                    })
                pay_amount -= transport_line.total_amount
                total_paid += transport_line.total_amount
            elif transport_line.term_state == 'due' and pay_amount < transport_line.total_amount:
                transport_line.write({
                    'total_paid': transport_line.total_paid + pay_amount,
                    'paid_date': str(datetime.today().date()),
                    'term_state': 'due', 
                    })
                total_paid += pay_amount
                pay_amount = 0.0
        current_state = self.term_state;
        self.write({'total_paid':self.total_paid+total_paid, 'fine_amount':fine_amount,
                    'term_state': status if self.amount == self.total_paid else current_state})
        self.create_receipt()
        self.update_ledger()
        self.pay_amount = 0.0
        self.payment_mode_id = self.is_show_cheque_dd_details = self.is_show_card_details = self.transaction_type = self.bank_machine_id = self.bank_machine_type_id = self.bank_name = False
        self.card_holder_name = self.card_number = self.card_type = self.mid_no = self.tid_no = self.cheque_dd = self.cheque_date = None

class TransportFeesCollection(models.Model):
    _name = 'transport.fees.collection'

    due_date = fields.Date(string='Due Date')
    amount = fields.Float('Amount')
    fine_amount = fields.Float('Fine Amount')
    total_paid = fields.Float('Total Paid')
    due_amount = fields.Float(compute='_compute_due_amount',string='Due Amount')
    total_amount = fields.Float(compute='_compute_total_amount', string='Total Amount')
    term_state = fields.Selection([('due', 'Due'), ('processing','Processing'),('paid', 'Paid')], 'Status')
    stud_collection_id = fields.Many2one('student.fees.collection', 'Student Collection')
    paid_date = fields.Date(string='Paid Date')
    
    @api.multi
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.amount + record.fine_amount
    
    @api.multi
    def _compute_due_amount(self):
        for record in self:
            record.due_amount = record.total_amount - record.total_paid 
        
    # @api.multi
    # def calculate_fine_amount(self):
    #     for line in self:
    #         d1 = datetime.strptime(line.due_date, "%Y-%m-%d").date()
    #         d2 = date.today()
    #         delta = d2 - d1
    #         due_week = datetime.strptime(line.due_date, "%Y-%m-%d").isocalendar()[1]
    #         current_week = date.today().isocalendar()[1]
    #         if d1 < d2:
    #             if line.stud_collection_id.collection_id.school_id.fine_type == 'day':
    #                 line.fine_amount = line.stud_collection_id.collection_id.school_id.fine_amount * delta.days
    #             elif line.stud_collection_id.collection_id.school_id.fine_type == 'month':
    #                 line.fine_amount = line.stud_collection_id.collection_id.school_id.fine_amount * delta.months


class Accountmoveline(models.Model):
    _inherit = "account.move.line"

    fees_collection_id = fields.Many2one('pappaya.fees.collection','Fees Collection')
    bank_id = fields.Many2one('branch.bank.account.mapping', 'Deposited Bank')


class Accountmove(models.Model):
    _inherit = "account.move"

    fees_collection_id = fields.Many2one('pappaya.fees.collection','Fees Collection')
