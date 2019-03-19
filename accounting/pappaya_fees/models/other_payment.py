# -*- coding: utf-8 -*-
from datetime import datetime
import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class OperatingUnitInherit(models.Model):
    _inherit = 'operating.unit'

    @api.multi
    def action_other_payment_info(self):
        action = self.env.ref('pappaya_fees.action_other_payment_configuration').read()[0]
        action['domain'] = [('branch_id', 'in', self.ids)]
        return action


class other_payment_configuration(models.Model):
    _name = 'other.payment.configuration'
    _description = 'Other Payment Configuration'
    _rec_name = 'branch_id'

    branch_id = fields.Many2one('operating.unit', 'Branch',
                                default=lambda self: self.env.user.default_operating_unit_id)
    academic_year_id = fields.Many2one('academic.year', 'Academic Year',
                                       default=lambda self: self.env['academic.year'].search(
                                           [('is_active', '=', True)]))
    name = fields.Char('Reference', size=100)
    other_payment_configuration_line = fields.One2many('other.payment.configuration.line', 'other_payment_config_id',
                                                       'Other Payment Lines')
    description = fields.Text('Description', size=300)

    @api.model
    def default_get(self, fields):
        res = super(other_payment_configuration, self).default_get(fields)
        if 'active_model' in self._context and self._context['active_model'] == 'operating.unit':
            res['branch_id'] = int(self._context['active_id'])
        return res

    @api.constrains('branch_id', 'academic_year_id')
    def _check_unique(self):
        if self.sudo().search_count(
                [('branch_id', '=', self.branch_id.id), ('academic_year_id', '=', self.academic_year_id.id)]) > 1:
            raise ValidationError("For given Branch and Academic year record already exists!")


class other_payment_configuration_line(models.Model):
    _name = 'other.payment.configuration.line'
    _rec_name = 'fee_head_id'

    @api.constrains('amount')
    def check_amount(self):
        if self.amount <= 0.0:
            raise ValidationError('Please enter the valid Amount..!')

    other_payment_config_id = fields.Many2one('other.payment.configuration', 'Other Payment Config')
    fee_head_id = fields.Many2one('pappaya.fees.head', 'Fee Type')
    fee_sub_head_id = fields.Many2one('pappaya.fees.sub.head', 'Sub Fee Type')
    amount = fields.Float('Amount')
    sgst = fields.Float('SGST %')
    cgst = fields.Float('CGST %')
    total_amount = fields.Float(compute='_compute_total_amount', string='Total')
    description = fields.Text('Description', size=300)

    @api.multi
    @api.depends('sgst', 'cgst', 'amount')
    @api.onchange('sgst', 'cgst', 'amount')
    def _compute_total_amount(self):
        for record in self:
            sgst_amount = (record.amount * record.sgst) / 100 if record.sgst else 0.0
            cgst_amount = (record.amount * record.cgst) / 100 if record.cgst else 0.0
            record.total_amount = (record.amount + sgst_amount + cgst_amount)

    @api.constrains('fee_head_id', 'fee_sub_head_id', 'other_payment_config_id')
    def _check_unique(self):
        if self.sudo().search_count(
                [('fee_head_id', '=', self.fee_head_id.id), ('fee_sub_head_id', '=', self.fee_sub_head_id.id),
                 ('other_payment_config_id', '=', self.other_payment_config_id.id)]) > 1:
            raise ValidationError("Given Fee Type and Sub Fee Type already exists!")

    @api.onchange('amount')
    def onchange_amount(self):
        if self.amount and self.amount <= 0.0:
            raise ValidationError('Please enter the valid Amount..!')

    @api.onchange('sgst')
    def onchange_sgst(self):
        if self.sgst and self.sgst < 0.0:
            raise ValidationError('Please enter the valid SGST..!')

    @api.onchange('cgst')
    def onchange_cgst(self):
        if self.cgst and self.cgst < 0.0:
            raise ValidationError('Please enter the valid CGST..!')


class pappaya_other_payment(models.Model):
    _name = 'pappaya.other.payment'
    _description = 'Other Payments'
    _rec_name = 'student_id'

    academic_year_id = fields.Many2one('academic.year', 'Academic Year',
                                       default=lambda self: self.env['academic.year'].search(
                                           [('is_active', '=', True)]))
    branch_id = fields.Many2one('operating.unit', 'Branch')
    branch_code = fields.Char(related='branch_id.code', string='Code')
    admission_id = fields.Many2one('pappaya.admission', 'Admission No')
    student_id = fields.Many2one('res.partner', 'Student Name')
    father_name = fields.Char(string='Father Name', size=100)
    # Amount Details
    amount_collected = fields.Float('Amount Collected')
    tax_collected = fields.Float('Tax Collected')
    balance_amount = fields.Float('Balance Amount')
    balance_tax = fields.Float('Balance Tax')

    # Receipt Information
    state = fields.Selection([('draft', 'Draft'), ('processing', 'Processing'), ('paid', 'Paid')], 'Status',
                             default='draft')
    payment_date = fields.Date('Date', default=fields.Date.context_today)

    payment_head = fields.Many2one('pappaya.fees.head', 'Head')
    payment_sub_head = fields.Many2one('pappaya.fees.sub.head', 'Sub Fee Type')
    amount = fields.Float(string='Amount')

    payment_mode_id = fields.Many2one('pappaya.paymode', 'Payment Mode')
    transaction_type = fields.Many2one('pappaya.master', 'Transaction Type')

    # Card Details
    card_holder_name = fields.Char('Card Holder Name', size=100)
    card_number = fields.Char('Card Number', size=20)
    # card_type = fields.Many2one('pappaya.master','Card Type')
    card_type = fields.Char('Card Type')
    bank_machine_id = fields.Many2one('bank.machine', 'Bank Machine')
    bank_machine_type_id = fields.Many2one('pappaya.master', 'Bank Machine Type',
                                           related='bank_machine_id.bank_machine_type_id')
    mid_no = fields.Char('M.I.D.No(last 6 digits)', size=30)
    tid_no = fields.Char('T.I.D.No', size=30)
    # Cheque Details
    cheque_dd = fields.Char('Cheque/DD No', size=30)
    cheque_date = fields.Date('Cheque Date')
    bank_name = fields.Many2one('res.bank', 'Bank Name')
    remarks = fields.Text('Remarks', size=300)
    is_fee_created = fields.Boolean('Is Fee Created?')
    is_paid = fields.Boolean('Is Paid?', default=False)
    is_show_card_details = fields.Boolean('Show Card Details')
    is_show_cheque_dd_details = fields.Boolean('Is Show Cheque Details')
    payment_option = fields.Selection([('pay_amount', 'Pay Amount'), ('fee_adjustment', 'Fee Adjustment')],
                                      "Pay Option", default='pay_amount')
    from_fee_head_id = fields.Many2one('pappaya.fees.head', string='From Fee Type')
    caution_deposit_amt = fields.Float(string='Caution Deposit')
    student_wallet_amt = fields.Float(string='Pocket Money')
    is_caution_amt = fields.Boolean(string='Is Caution Amount ?')
    is_pocket_amt = fields.Boolean(string='Is Pocket Amount ?')
    is_transport = fields.Boolean('Is Show Transport?')
    other_payment_type = fields.Selection([('other_pay', 'Other Payment'), ('transport_pay', 'Transport Payment'),('material_pay','Material Pay')],
                                          string='Other payment type', default='other_pay')
    transport_slab_id = fields.Many2one('pappaya.transport.stop', string='Transport Slab')
    service_route_id = fields.Many2one('pappaya.transport.route', string='Service Route')
    pos_reference_no = fields.Char('POS Ref No.')
    pos_api_response = fields.Text('POS API Response')
    receipt_id = fields.Many2one('pappaya.fees.receipt', 'Receipt')
    is_material_fee_editable = fields.Boolean('Is Material Fee Editable?', default=False)

    @api.onchange('other_payment_type')
    def onchange_other_payment_type(self):
        self.update({
            'material_set_ids':False, 'transport_slab_id':False, 'service_route_id':False, 'payment_head':False, 'payment_sub_head':False, 'amount':0.0
            })
        if self.other_payment_type == 'material_pay':
            self.payment_head = self.env['pappaya.fees.head'].sudo().search([('is_material_fee','=',True)], limit=1).id 
            fee_collection_id = self.env['pappaya.fees.collection'].search(
                [('academic_year_id', '=', self.academic_year_id.id),
                 ('enquiry_id', '=', self.admission_id.id)], limit=1)
            collection_line = self.env['student.fees.collection'].search([('collection_id', '=', fee_collection_id.id), 
                                                                        ('name.is_material_fee', '=', True)], limit=1)
            if collection_line and collection_line.term_state == 'due':
                self.material_set_ids = self.admission_id.material_set_ids.ids
            else:
                self.is_material_fee_editable = True
   
    @api.onchange('cheque_dd')
    def onchange_cheque_dd(self):
        for rec in self:
            if rec.cheque_dd:
                cheque_dd = re.match('^[\d]*$', rec.cheque_dd)
                if not cheque_dd:
                    raise ValidationError(_("Please enter a valid Cheque/DD Number"))

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        if self.branch_id.is_transport and self.admission_id.residential_type_id.code != 'hostel':
            self.is_transport = True

    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")

    @api.constrains('amount')
    def check_amount(self):
        if self.amount <= 0.0:
            raise ValidationError('Please enter the valid Amount..!')
        fee_collection_id = self.env['pappaya.fees.collection'].search([('academic_year_id', '=', self.academic_year_id.id),
                                                                        ('enquiry_id', '=', self.admission_id.id)], limit=1)
        if not fee_collection_id:
            student_name = self.student_id.name if self.student_id else self.admission_id.name
            raise ValidationError("No fee collection record found for given student ("+str(student_name)+")" +" and \n for given academic year ("+str(self.academic_year_id.name)+")")            
            

    @api.one
    @api.constrains('payment_date')
    def _check_payment_date(self):
        # if self.payment_date and self.payment_date < self.academic_year_id.start_date or self.payment_date > self.academic_year_id.end_date:
        #     raise ValidationError('Date should be within the academic year..!')
        if self.payment_date > str(datetime.today().date()):
            raise ValidationError("Date should not be in future date.!")

    @api.onchange('payment_date')
    def onchange_payment_date(self):
        self._check_payment_date()

    @api.onchange('amount')
    def onchange_amount(self):
        if self.amount and self.amount <= 0.0:
            raise ValidationError('Please enter the valid Amount..!')                    

    @api.onchange('payment_head', 'branch_id', 'academic_year_id')
    def onchange_payment_head(self):
        domain = {};
        domain['payment_head'] = [('id', 'in', [])];domain['payment_sub_head'] = [('id', 'in', [])]
        other_payment_config_obj = self.env['other.payment.configuration']
        other_payment_config_id = other_payment_config_obj.search([('branch_id', '=', self.branch_id.id), ('academic_year_id', '=', self.academic_year_id.id)])
        if other_payment_config_id:
            domain['payment_head'] = [('id', 'in', other_payment_config_id.other_payment_configuration_line.mapped('fee_head_id').ids)]
        if self.payment_head and other_payment_config_id:
            domain['payment_sub_head'] = [('id', 'in', other_payment_config_id.other_payment_configuration_line.mapped('fee_sub_head_id').ids)]
        return {'domain': domain}

    @api.onchange('payment_head', 'payment_sub_head', 'transport_slab_id', 'service_route_id')
    def onchange_payment_sub_head(self):
        if self.other_payment_type == 'transport_pay':
            self.amount = self.transport_slab_id.amount
            transport_head = self.env['pappaya.fees.head'].sudo().search([('is_transport_fee', '=', True)], limit=1)
            if transport_head:
                self.payment_head = transport_head.id
        else:
            other_payment_config_obj = self.env['other.payment.configuration']
            other_payment_config_id = other_payment_config_obj.search([('branch_id', '=', self.branch_id.id), ('academic_year_id', '=', self.academic_year_id.id)])
            if other_payment_config_id:
                if self.payment_head and self.payment_sub_head:
                    self.amount = other_payment_config_obj.other_payment_configuration_line.search(
                        [('other_payment_config_id', '=', other_payment_config_id.id),
                         ('fee_head_id', '=', self.payment_head.id),
                         ('fee_sub_head_id', '=', self.payment_sub_head.id)]).total_amount
                elif self.payment_head:
                    self.amount = other_payment_config_obj.other_payment_configuration_line.search(
                        [('other_payment_config_id', '=', other_payment_config_id.id),
                         ('fee_head_id', '=', self.payment_head.id), ('fee_sub_head_id', '=', False)]).total_amount
                else:
                    self.amount = 0.0

    @api.onchange('payment_mode_id')
    def onchange_payment_mode_id(self):
        self.is_show_card_details = True if self.payment_mode_id.is_card else False
        self.is_show_cheque_dd_details = True if self.payment_mode_id.is_cheque else False
        if self.payment_mode_id.is_card:
            account_mapping_id = self.env['branch.bank.account.mapping'].search(
                [('operating_unit_id', '=', self.branch_id.id), ('is_card', '=', True)], order='id')
            if len(account_mapping_id.ids) == 1:
                self.bank_name = account_mapping_id.bank_id.id;
                self.bank_machine_id = account_mapping_id.bank_machine_id.id
                self.bank_machine_type_id = account_mapping_id.bank_machine_type_id.id;
                self.mid_no = account_mapping_id.mid_number
                self.tid_no = account_mapping_id.tid_number
            else:
                self.bank_name = self.bank_machine_id = self.bank_machine_type_id = self.mid_no = self.tid_no = False

    @api.onchange('bank_name')
    def onchange_bank_name(self):
        if self.bank_name and self.payment_mode_id.is_card:
            account_mapping_id = self.env['branch.bank.account.mapping'].search(
                [('operating_unit_id', '=', self.branch_id.id), ('is_card', '=', True),
                 ('bank_id', '=', self.bank_name.id)], limit=1)
            if account_mapping_id:
                self.bank_name = account_mapping_id.bank_id.id;
                self.bank_machine_id = account_mapping_id.bank_machine_id.id
                self.bank_machine_type_id = account_mapping_id.bank_machine_type_id.id;
                self.mid_no = account_mapping_id.mid_number
                self.tid_no = account_mapping_id.tid_number
            else:
                self.bank_name = self.bank_machine_id = self.bank_machine_type_id = self.mid_no = self.tid_no = False

    @api.multi
    def action_other_pay_receipt_info(self):
        action = self.env.ref('pappaya_fees.action_pappaya_fees_receipt_id').read()[0]
        action['domain'] = [('id', '=', self.receipt_id.id)]
        return action

    @api.multi
    def action_pay_fees(self):
        for record in self:
            fee_collection_id = self.env['pappaya.fees.collection'].search(
                [('academic_year_id', '=', record.academic_year_id.id),
                 ('enquiry_id', '=', record.admission_id.id)], limit=1)
            if not fee_collection_id:
                student_name = record.student_id.name if record.student_id else record.admission_id.name
                raise ValidationError("No fee collection record found for given student ("+str(student_name)+")" +" and \n for given academic year ("+str(record.academic_year_id.name)+")")
            if fee_collection_id:
                if self.other_payment_type == 'transport_pay':
                    collection_line = self.env['student.fees.collection'].search(
                        [('collection_id', '=', fee_collection_id.id), ('name.is_transport_fee', '=', True)], limit=1)
                    if collection_line and not self.is_fee_created:
                        collection_line.gst_total += record.amount;
                        collection_line.amount += record.amount;
                        collection_line.enquiry_id = record.student_id.admission_id.id
                        collection_line.res_adj_amt = 0.0;
                        collection_line.term_state = 'due';
                        collection_line.other_payment_id = record.id
                    else:
                        if not self.is_fee_created:
                            self.env['student.fees.collection'].create({
                                'collection_id': fee_collection_id.id,
                                'name': self.env['pappaya.fees.head'].search([('is_transport_fee', '=', True)],
                                                                             limit=1).id,
                                'gst_total': record.amount,
                                'cgst': 0.0,
                                'sgst': 0.0,
                                'amount': record.amount,
                                'res_adj_amt': 0.00,
                                'due_amount': record.amount,
                                'total_paid': 0.0,
                                'term_state': 'due',
                                'enquiry_id': record.student_id.admission_id.id,
                                'other_payment_id': record.id,
                            })
                            self.is_fee_created = True
                elif self.other_payment_type == 'material_pay':
                    collection_line = self.env['student.fees.collection'].search([('collection_id', '=', fee_collection_id.id), 
                                                                                ('name.is_material_fee', '=', True)], limit=1)
                    if collection_line and collection_line.term_state == 'due':
                        collection_line.other_payment_id = record.id; collection_line.enquiry_id = record.student_id.admission_id.id
                    elif collection_line and record.is_material_fee_editable and not self.is_fee_created:
                        collection_line.gst_total += record.amount;
                        collection_line.amount += record.amount;
                        collection_line.enquiry_id = record.student_id.admission_id.id
                        collection_line.res_adj_amt = 0.0;
                        collection_line.term_state = 'due';
                        collection_line.other_payment_id = record.id
                    else:
                        if not self.is_fee_created:
                            self.env['student.fees.collection'].create({
                                'collection_id': fee_collection_id.id,
                                'name': self.env['pappaya.fees.head'].search([('is_material_fee', '=', True)],
                                                                             limit=1).id,
                                'gst_total': record.amount,
                                'cgst': 0.0,
                                'sgst': 0.0,
                                'amount': record.amount,
                                'res_adj_amt': 0.00,
                                'due_amount': record.amount,
                                'total_paid': 0.0,
                                'term_state': 'due',
                                'enquiry_id': record.student_id.admission_id.id,
                                'other_payment_id': record.id,
                            })
                            self.is_fee_created = True
                else:
                    collection_line = self.env['student.fees.collection'].search(
                        [('collection_id', '=', fee_collection_id.id), ('name', '=', record.payment_head.id)])
                    if collection_line and not self.is_fee_created:
                        collection_line.gst_total += record.amount;
                        collection_line.amount += record.amount;
                        collection_line.enquiry_id = record.student_id.admission_id.id
                        collection_line.res_adj_amt = 0.0;
                        collection_line.term_state = 'due';
                        collection_line.other_payment_id = record.id
                        self.is_fee_created = True
                    else:
                        if not self.is_fee_created:
                            self.env['student.fees.collection'].create({
                                'collection_id': fee_collection_id.id,
                                'name': record.payment_head.id,
                                'gst_total': record.amount,
                                'cgst': 0.0,
                                'sgst': 0.0,
                                'amount': record.amount,
                                'res_adj_amt': 0.00,
                                'due_amount': record.amount,
                                'total_paid': 0.0,
                                'term_state': 'due',
                                'enquiry_id': record.student_id.admission_id.id,
                                'other_payment_id': record.id,
                            })
                            self.is_fee_created = True

                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'pappaya.fees.collection',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'context': {'other_payment': record.id},
                    'res_id': fee_collection_id.id,
                    'view_id': self.env.ref('pappaya_fees.pappaya_fees_collection_form', False).id,
                    'target': 'new',
                }

    @api.onchange('payment_option', 'from_fee_head_id', 'payment_head')
    @api.constrains('amount', 'from_fee_head_id')
    def onchange_payment_option(self):
        if self.admission_id and self.payment_option == 'fee_adjustment':
            # Updating available caution deposit and pocket money from student profile
            if self.from_fee_head_id.is_caution_deposit_fee:
                self.is_caution_amt = True
                self.is_pocket_amt = False
            if self.from_fee_head_id.is_pocket_money:
                self.is_caution_amt = False
                self.is_pocket_amt = True
            self.caution_deposit_amt = self.admission_id.partner_id.caution_deposit
            self.student_wallet_amt = self.admission_id.partner_id.student_wallet_amount

            # Updating from fee head
            if self.admission_id:
                pfc_obj = self.env['pappaya.fees.collection'].search([('enquiry_id', '=', self.admission_id.id)])
                stu_transaction_ids = pfc_obj.fees_collection_line
                from_fee_heads = []
                for fc_obj in stu_transaction_ids:
                    if (fc_obj.name.is_caution_deposit_fee or fc_obj.name.is_pocket_money) and fc_obj.name.name != self.payment_head.name:
                        from_fee_heads.append(fc_obj.name.id)
                if len(from_fee_heads) == 0:
                    raise ValidationError(
                        'There is no adjustable fees/Adjustable amount should be lesser than or equal to Other payment Amount')
                return {'domain': {'from_fee_head_id': [('id', 'in', from_fee_heads)]}}

            if self.admission_id and len(self.search(
                    [('admission_id', '=', self.admission_id.id), ('state', 'in', ['draft', 'processing']),
                     ('payment_option', '=', 'fee_adjustment')])) > 1:
                raise ValidationError('Already record existed for given admission in Draft or Processing stage')
            if self.from_fee_head_id and self.from_fee_head_id.is_caution_deposit_fee and self.caution_deposit_amt == 0:
                raise ValidationError('No amount in Caution Deposit')
            if self.from_fee_head_id and self.from_fee_head_id.is_pocket_money and self.student_wallet_amt == 0:
                raise ValidationError('No amount in Pocket Money')
            if self.amount and (self.amount == 0 or self.amount < 0):
                raise ValidationError('Amount should be greater than 0.')

    @api.multi
    def action_fees_adjustment(self):
        if self.from_fee_head_id and self.from_fee_head_id.is_caution_deposit_fee and self.caution_deposit_amt == 0:
            raise ValidationError('No amount in Caution Deposit')
        if self.from_fee_head_id and self.from_fee_head_id.is_pocket_money and self.student_wallet_amt == 0:
            raise ValidationError('No amount in Pocket Money')
        if self.amount and (self.amount == 0 or self.amount < 0):
            raise ValidationError('Amount should be greater than 0.')
        if self.admission_id and self.amount > 0:
            fee_collection_id = self.env['pappaya.fees.collection'].search([('enquiry_id', '=', self.student_id.admission_id.id)], limit=1)
            if fee_collection_id:
                collection_line = self.env['student.fees.collection'].search([('collection_id', '=', fee_collection_id.id), ('name', '=', self.payment_head.id)])
                if collection_line and not self.is_fee_created:
                    collection_line.gst_total += self.amount
                    collection_line.amount += self.amount
                    collection_line.enquiry_id = self.student_id.admission_id.id
                    collection_line.adjusted_amount += self.amount
                    collection_line.total_paid = 0.0 if (collection_line.adjusted_amount + collection_line.res_adj_amt == collection_line.gst_total) else (collection_line.total_paid + self.amount)
                    collection_line.write({'term_state': 'paid' if collection_line.due_amount == 0 else 'due',  'due_amount' : collection_line.amount - collection_line.total_paid - collection_line.res_adj_amt - collection_line.fine_amount - collection_line.adjusted_amount })
                    collection_line.other_payment_id = self.id
                    self.is_fee_created = True
                    self.state = 'paid'
                else:
                    if not self.is_fee_created:
                        self.env['student.fees.collection'].create({
                            'collection_id': fee_collection_id.id,
                            'name': self.payment_head.id,
                            'gst_total': self.amount,
                            'cgst': 0.0,
                            'sgst': 0.0,
                            'amount': self.amount,
                            'total_paid': self.amount,
                            'term_state': 'paid',
                            'enquiry_id': self.student_id.admission_id.id,
                            'other_payment_id': self.id,
                            'adjusted_amount': self.amount,
                        })
                        self.is_fee_created = True
                        self.state = 'paid'

                ledger_obj = self.env['pappaya.fees.ledger'].search([('enquiry_id', '=', self.admission_id.id)])
                if ledger_obj:
                    self.env['pappaya.fees.refund.ledger'].create({
                        'fees_ledger_id': ledger_obj.id,
                        'amount': self.amount,
                        'posting_date': datetime.today().date(),
                        'transaction_remarks': 'Other Payment : ' + str(self.from_fee_head_id.name) + '-' + str(self.payment_head.name)
                    })

        print ('\n', self.from_fee_head_id.is_caution_deposit_fee, self.from_fee_head_id.is_pocket_money,
               self.payment_head.is_caution_deposit_fee, self.payment_head.is_pocket_money, self.amount,
               self.admission_id.partner_id.caution_deposit, self.admission_id.partner_id.student_wallet_amount)

        if self.from_fee_head_id and self.from_fee_head_id.is_caution_deposit_fee:
            self.admission_id.partner_id.caution_deposit -= self.amount
        if self.from_fee_head_id and self.from_fee_head_id.is_pocket_money:
            self.admission_id.partner_id.student_wallet_amount -= self.amount
        if self.payment_head and self.payment_head.is_caution_deposit_fee:
            self.admission_id.partner_id.caution_deposit += self.amount
        if self.payment_head and self.payment_head.is_pocket_money:
            self.admission_id.partner_id.student_wallet_amount += self.amount
