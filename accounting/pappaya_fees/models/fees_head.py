# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class pappaya_fees_sub_head(models.Model):
    _name = 'pappaya.fees.sub.head'

    fees_head_id = fields.Many2one('pappaya.fees.head', 'Fee Type')
    name = fields.Char('Sub Fee Type', size=100)
    description = fields.Text('Description', size=300)


class Pappaya_fees_head(models.Model):
    _name = 'pappaya.fees.head'

    school_id = fields.Many2one('res.company', 'Branch', default=lambda self: self.env.user.company_id)
    name = fields.Char('Name', size=50)
    code = fields.Char('Code', size=5)
    fee_type = fields.Selection(
        [('term_fees', 'Term Fees'), ('admission_fees', 'Admission Fees'), ('annual_fee', 'Annual Fee'),
         ('transport_fees', 'Transport Fees'), ('material_fees', 'Material Fees'),
         ('uniform_fees', 'Uniform Fees'), ('other_fees', 'Other Fees')], string='Type')
    student_type = fields.Selection(
        [('day', 'Day'), ('hostel', 'Hostel'), ('semi_residential', 'Semi Residential'), ('both', 'All')],
        'Student Type')
    residential_type_ids = fields.Many2many('residential.type', string='Student Residential Type')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('both', 'Both')], 'Gender')
    medium_ids = fields.Many2many('pappaya.master', string='Medium')
    # List of fee categories
    is_show_by_default = fields.Boolean('Is show by Default in Fee Structure?')
    is_compulsory_fee = fields.Boolean('Is Compulsory Fee?')
    is_course_fee = fields.Boolean('Is Course Fee?')
    is_reservation_fee = fields.Boolean('Is Reservation Fee?')
    is_transport_fee = fields.Boolean('Is Transport Fee?')
    is_nslate_fee = fields.Boolean('Is Nslate Fee?')
    is_caution_deposit_fee = fields.Boolean('Is Caution Deposit Fee?')
    is_refundable_fee = fields.Boolean('Is Refundable Fee?')
    is_material_fee = fields.Boolean('Is Material Fee?')
    is_uniform_fee = fields.Boolean('Is Uniform Fee?')
    is_library_fee = fields.Boolean('Library Fee')
    is_soa_fee = fields.Boolean('Is Sale Of Application Fee?')
    is_pocket_money = fields.Boolean('Is Pocket Money?')
    # Fields Related to other payments
    is_other_payment = fields.Boolean('Is Other Payment?')
    is_course_fee_component = fields.Boolean('Is Course Fee Component?')
    amount = fields.Float('Amount')
    pappaya_fees_sub_head_ids = fields.One2many('pappaya.fees.sub.head', 'fees_head_id', 'Sub Ledger')
    # These fields are used to map admission with accounting at the backend
    product_id = fields.Many2one('product.product', 'Product Name', domain=[('type', '=', 'service')])
    credit_account_id = fields.Many2one('account.account', 'Credit Account')
    debit_account_id = fields.Many2one('account.account', 'Debit Account')
    journal_id = fields.Many2one('account.journal', 'Journal')
    entity_id = fields.Many2one('operating.unit', string='Entity')

    @api.one
    @api.constrains('name', 'gender', 'is_pocket_money', 'is_course_fee', 'is_reservation_fee', 'is_transport_fee',
                    'is_nslate_fee', 'is_uniform_fee','is_material_fee')
    def check_name_exists(self):
        if self.name:
            if len(self.search([('name', '=', self.name)])) > 1:
                raise ValidationError('Name already exists')
        if self.is_course_fee:
            if len(self.search([('is_course_fee', '=', True)])) > 1:
                raise ValidationError('Course Fee already defined')
        if self.is_reservation_fee:
            if len(self.search([('is_reservation_fee', '=', True)])) > 1:
                raise ValidationError('Reservation Fee already defined')
            if self.is_refundable_fee:
                raise ValidationError('Reservation Fee is not a Refundable')
        if self.is_transport_fee:
            if len(self.search([('is_transport_fee', '=', True)])) > 1:
                raise ValidationError('Transport Fee already defined')
        if self.is_nslate_fee:
            if len(self.search([('is_nslate_fee', '=', True)])) > 1:
                raise ValidationError('Nslate Fee already defined')
        if self.is_uniform_fee:
            if len(self.search(
                    ['|', ('gender', '=', 'both'), ('gender', '=', 'male'), ('is_uniform_fee', '=', True)])) > 1:
                raise ValidationError('Uniform Fee already defined')
            if len(self.search(
                    ['|', ('gender', '=', 'both'), ('gender', '=', 'female'), ('is_uniform_fee', '=', True)])) > 1:
                raise ValidationError('Uniform Fee already defined')
        if self.is_pocket_money:
            if len(self.search([('is_pocket_money', '=', True)])) > 1:
                raise ValidationError('Pocket Money Fee already defined')
        if self.is_material_fee:
            if len(self.search([('is_material_fee', '=', True)])) > 1:
                raise ValidationError('Material Fee already defined')


    @api.onchange('fee_type')
    def onchange_fee_type(self):
        if self.fee_type == 'material_fees':
            self.is_material_fee = True
        else:
            self.is_material_fee = False
        if self.fee_type == 'transport_fees':
            self.is_transport_fee = True
        else:
            self.is_transport_fee = False
        if self.fee_type == 'uniform_fees':
            self.is_uniform_fee = True
        else:
            self.is_uniform_fee = False

    @api.onchange('is_reservation_fee')
    def onchange_reservation_fee(self):
        if self.is_reservation_fee:
            self.is_refundable_fee = False

    #     @api.model
    #     def create(self,  vals):
    #         if 'name' and 'school_id' in vals:
    #             user_type_id = self.env['account.account.type'].search([('name','=','Income')]).id
    #             count = self.env['account.account'].search_count([])
    #             count += 100000
    #             journal_obj = self.env['account.journal'].search([('code','=','NARFC')])
    #             if not journal_obj:
    #                 receivable_id = self.env['account.account.type'].search([('name','=','Receivable')]).id
    #                 nafc_rec_account_obj = self.env['account.account'].create({'name':'Narayana Fee Collection Receivable',
    #                                                                            'code': str(count),
    #                                                                            'reconcile': True,
    #                                                                            'user_type_id': receivable_id})
    #
    #                 count += 1
    #                 nafc_income_account_obj = self.env['account.account'].create({'name': 'Narayana Fee Collection Income',
    #                                                                               'code': str(count),
    #                                                                               'user_type_id': user_type_id})
    #
    #                 journal_obj = self.env['account.journal'].create({'name': 'Narayana Fee Collection',
    #                                                                   'type': 'sale',
    #                                                                   'code': 'NARFC',
    #                                                                   'default_debit_account_id': nafc_income_account_obj.id,
    #                                                                   'default_credit_account_id': nafc_income_account_obj.id})
    #             count += 1
    #             if vals['is_reservation_fee']:
    #                 liabilities_id = self.env['account.account.type'].search([('name','=','Current Liabilities')]).id
    #                 prod_chat_of_account_obj = self.env['account.account'].create({'name': 'Narayana Fee Collection Current Liabilities',
    #                                                                                'code': str(count),
    #                                                                                'user_type_id': liabilities_id})
    #             else:
    #                 prod_chat_of_account_obj = self.env['account.account'].create({'name':vals['name'],
    #                                                                                'code': str(count),
    #                                                                                'user_type_id': user_type_id})
    #             vals['chat_of_account_id'] = prod_chat_of_account_obj.id

    #             prod_template_obj = self.env['product.product'].create({'name': vals['name'],
    #                                                                      'taxes_id': None,
    #                                                                      'sale_ok': True,
    #                                                                      'purchase_ok': False,
    #                                                                      'supplier_taxes_id': None,
    #                                                                      'property_account_income_id': vals['chat_of_account_id'],
    #                                                                      'company_id': vals['school_id'],
    #                                                                      'type':'service'})
    #             vals['product_id'] = prod_template_obj.id

    #             if journal_obj:
    #                 vals['journal_id'] = journal_obj.id
    #         return super(Pappaya_fees_head, self).create( vals)

    #     @api.multi
    #     def write(self, vals):
    #         if 'name' in vals.keys() and vals.get('name'):
    #             self.product_id.name = vals.get('name')
    #             self.chat_of_account_id.name = vals.get('name')
    #         return super(Pappaya_fees_head, self).write(vals)

    @api.multi
    def unlink(self):
        raise ValidationError(_("This record is considered as master record.\nYou are not allowed to delete it."))
