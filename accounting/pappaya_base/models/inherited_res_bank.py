# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class ResBank(models.Model):
    _inherit = "res.bank"

    @api.constrains('account_number_length')
    def _check_account_number_length(self):
        """Check Account Number Length should be 10 to 20"""
        if (self.account_number_length < 10) or (self.account_number_length > 20):
            raise ValidationError('Please enter the valid Maximum Account Number Length..!')

    name = fields.Char('Bank Name',required=True,size=60)
    street = fields.Char('Address 1',size=40)
    street2 = fields.Char('Address 2',size=40)
    district_id = fields.Many2one("state.district", string='District', ondelete='restrict')
    city = fields.Many2one("pappaya.city", string='City', ondelete='restrict')
    phone = fields.Char(size=15)
    mobile = fields.Char(string='Mobile', size=10)
    email = fields.Char(size=60)
    country = fields.Many2one('res.country', string="Country", domain=[('is_active','=',True)], default=lambda self: self.env.user.company_id.country_id.id)
    state = fields.Many2one('res.country.state', string='State', domain=[('country_id.is_active', '=', True)])
    zip = fields.Char('Pin Code', size=6)
    bic = fields.Char('Bank Identifier Code', size=5, index=True, help="Sometimes called BIC or Swift.",)
    account_number_length = fields.Integer('Maximum Account Number Length')
    ifsc_code_prefix = fields.Char('IFSC Prefix', size=10)
    is_payroll_bank = fields.Boolean('Is Payroll Bank', default=False)
    office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    
    def _validate_vals(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        if 'phone' in vals.keys() and vals.get('phone'):
            self.env['res.company'].validate_phone(vals.get('phone'))
        if 'mobile' in vals.keys() and vals.get('mobile'):
            self.env['res.company'].validate_mobile(vals.get('mobile'))
        if 'email' in vals.keys() and vals.get('email'):
            self.env['res.company'].validate_email(vals.get('email'))
        if 'zip' in vals.keys() and vals.get('zip'):
            self.env['res.company'].validate_zip(vals.get('zip'))
        return True

    @api.multi
    @api.depends('name', 'bic')
    def name_get(self):
        result = []
        for bank in self:
            name = bank.name + (bank.bic and (' - ' + bank.bic) or '')
            result.append((bank.id, name))
        return result

        # res = super(ResBank, self).name_get()
        # result = []
        # if self._context.get('bankid') == 'bank_id':
        #     for bank in self:
        #         name_val = bank.name + (bank.bic and (' - ' + bank.bic) or '')
        #         result.append((bank.id, name_val))
        #     return result
        # return res
    
    @api.model
    def create(self, vals):
        self._validate_vals(vals)
        return super(ResBank, self).create(vals)

    @api.multi
    def write(self, vals):
        self._validate_vals(vals)
        return super(ResBank, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name','office_type_id')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name),(('office_type_id', '=', self.office_type_id.id))])) > 1:
            raise ValidationError("Bank already exists")
        
    @api.onchange('phone')
    def _onchange_phone(self):
        if self.phone:
            self.env['res.company'].validate_phone(self.phone)

    @api.onchange('mobile')
    def _onchange_mobile(self):
        if self.mobile:
            self.env['res.company'].validate_mobile(self.mobile)
    
    @api.onchange('email')
    def _onchange_email(self):
        if self.email:
            self.env['res.company'].validate_email(self.email)
     
    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            self.env['res.company'].validate_zip(self.zip)

class BankAccountBranch(models.Model):
    _name = "bank.account.branch"
    
    @api.constrains('name')
    def validate_ifsc_no(self):
        if len(self.name) < 1:
            raise ValidationError('Account Branch name is already exit.')
        
    name = fields.Char(required=True, size=50)
    description = fields.Text(string='Description', size=100)

    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")

class BankMachineType(models.Model):
    _name = 'bank.machine.type'
    
    name = fields.Char(string='Bank Machine Type', required=1, size=40)
    description = fields.Text(string='Description', size=100)

class BankMachine(models.Model):
    _name = 'bank.machine'
    
    name = fields.Char(string='Bank Machine', required=1, size=40)
    bank_machine_type_id = fields.Many2one('pappaya.master', string='Bank Machine Type')
    description = fields.Text(string='Description', size=100)

    @api.constrains('name', 'bank_machine_type_id')
    def check_bank_machine(self):
        if self.name and len(self.search([('name', '=ilike', self.name)])) > 1:
            raise ValidationError("Bank Machine name already exists.")
        if self.name and self.bank_machine_type_id and len(self.search([('name', '=ilike', self.name),('bank_machine_type_id', '=', self.bank_machine_type_id.id)])) > 1:
            raise ValidationError("Bank Machine already exists.")


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    
    ifsc_no = fields.Char('IFSC', size=11)
    emp_id = fields.Many2one('hr.employee','Employee')
    department_id = fields.Many2one('hr.department','Department', related="emp_id.department_id")
    job_id = fields.Many2one('hr.job','Designation', related="emp_id.job_id")
    
    acc_number = fields.Char('Account Number', required=True, size=30)
    bic = fields.Char('Bank Identifier Code', related="bank_id.bic")
    bank_acc_branch_id = fields.Many2one('bank.account.branch', string='Bank Account Branch')
    
    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for acc in self:
            name = str(acc.acc_number) + ' (' + str(acc.bank_id.name) + ')'
            result.append((acc.id, name))
        return result
    
    @api.constrains('emp_id')
    def validate_of_emp_id(self):
        if len(self.sudo().search([('emp_id', '=', self.emp_id.id),('acc_number', '=', self.acc_number)])) > 1:
            raise ValidationError("Account number is already exists for selected employee.")

    @api.constrains('ifsc_no')
    def validate_ifsc_no(self):
        if self.ifsc_no and len(self.ifsc_no) < 11:
            raise ValidationError('Please enter a valid 11 digit RTGS/IFSC')
