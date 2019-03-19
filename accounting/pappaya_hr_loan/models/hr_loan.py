# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import except_orm
from odoo.exceptions import ValidationError


class LoanInterest(models.Model):
    _name = 'loan.interest'
    _description = "Loan Interest"

    name = fields.Selection([('short_term', 'Short Term'), ('long_term', 'Long Term')], string="Loan Type", default='short_term')
    percentage = fields.Float(string="Int(%)")


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.one
    def _compute_loan_amount(self):
        total_paid = 0.0
        for record in self:
            total_amount = (record.loan_amount + ((record.loan_amount * record.loan_percent) / 100))
            for line in record.loan_lines:
                if line.paid:
                    total_paid += line.amount

            record.total_amount = total_amount
            record.total_paid_amount = total_paid
            record.balance_amount = record.total_amount - total_paid

    name = fields.Char(string="Loan Name", readonly=True)
    employee_ref = fields.Char(string="Employee ID")
    loan_type = fields.Selection([('short_term', 'Short Term'),
                                  ('long_term', 'Long Term')], string="Loan Type", required=True, readonly=True)
    short_term_installment = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')], string = "No Of Installments", readonly=True)
    long_term_installment = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9')
                                              , ('10', '10'), ('11', '11'), ('12', '12')], string="No Of Installments", readonly=True)
    loan_bool = fields.Boolean(string="Loan Boolean", default=False)
    loan_percent = fields.Float(string="Int(%)")
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True)
    date_of_joining = fields.Date(string='Date of Join', related="employee_id.date_of_joining", readonly=True)
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True, string="Department")
    installment = fields.Integer(string="No Of Installments", default=1)
    payment_date = fields.Date(string="Payment Start Date", required=True, readonly=True, default=fields.Date.today())
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    sureties_lines = fields.One2many('loan.sureties.lines', 'loan_id', string="Sureties Lines", index=True)
    emp_account_id = fields.Many2one('account.account', string="Loan Account")
    treasury_account_id = fields.Many2one('account.account', string="Treasury Account")
    journal_id = fields.Many2one('account.journal', string="Journal")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
    category_id = fields.Many2one('pappaya.employee.category', related="employee_id.category_id", string='Category', readonly=True)
    sub_category_id = fields.Many2one('hr.employee.subcategory', related="employee_id.sub_category_id", string='Sub Category', readonly=True)
    gross_salary = fields.Float('Gross Salary(Per Month)', related="employee_id.gross_salary", readonly=True)
    loan_amount = fields.Float(string="Loan Amount", required=True)
    total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_loan_amount')
    balance_amount = fields.Float(string="Balance Amount", compute='_compute_loan_amount')
    total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_loan_amount')
    installment_bool = fields.Boolean(string="Installment Bool", default=False)
    remarks = fields.Text(string="Remarks")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Requested'),
        ('approve', 'Approved'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    @api.constrains('loan_amount')
    def check_loan_amount(self):
        for record in self:
            if record.loan_type == 'short_term':
                if record.loan_amount > 0.0:
                    start_date = datetime.strptime(record.date, "%Y-%m-%d")
                    e_date = record.employee_id.date_of_joining
                    end_date = datetime.strptime(e_date, "%Y-%m-%d")
                    years = relativedelta(start_date, end_date).years
                    loan_amount = (2 * record.employee_id.gross_salary)
                    if years >= 1:
                        if record.loan_amount > loan_amount:
                            raise ValidationError("For short term loan, You cannot make loan request for 2 times more than your Gross Salary")
                    else:
                        raise ValidationError("For short term loan, You must have a minimum of 1 year continued service for this Company.")

                else:
                    raise ValidationError("Loan amount should not be 0.")

            if record.loan_type == 'long_term':
                if record.loan_amount > 0.0:
                    start_date = datetime.strptime(record.date, "%Y-%m-%d")
                    e_date = record.employee_id.date_of_joining
                    end_date = datetime.strptime(e_date, "%Y-%m-%d")
                    years = relativedelta(start_date, end_date).years
                    loan_amount = (5 * record.employee_id.gross_salary)
                    if years >= 2:
                        if record.loan_amount > loan_amount:
                            raise ValidationError("For long term loan, You cannot make loan request for 5 times more than your Gross Salary")
                    else:
                        raise ValidationError("For long term loan, You must have a minimum of 2 year continued service for this Company.")
                else:
                    raise ValidationError("Loan amount should not be 0.")


    @api.constrains('sureties_lines','loan_amount')
    def check_loan_sureties_lines(self):
        for record in self:
            if len(record.sureties_lines) < 2:
                raise ValidationError("2 Employees must be added for Surety ")

    @api.model
    def create(self, values):
        today = fields.Date.today()
        today_date = datetime.strptime(today, '%Y-%m-%d')
        next_year = int(today_date.year) + 1
        fin_string = str(next_year) + "-03-31"
        date_march = datetime.strptime(fin_string, '%Y-%m-%d')
        if 'payment_date' in values:
            if values['payment_date'] < today:
                raise ValidationError('You cannot make loan request for past dates.')

            payment_date = datetime.strptime(values['payment_date'], '%Y-%m-%d')
            if payment_date > date_march:
                raise ValidationError('You cannot make loan request for next financial years.')

        if 'sureties_lines' in values:
            if len(values['sureties_lines']) > 2:
                raise ValidationError('You cannot add more than 2 Sureties.')

        loan_count = self.env['hr.loan'].search_count([('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
                                                       ('balance_amount', '!=', 0)])

        if loan_count:
            raise ValidationError('The employee has already a pending installment')
        else:
            values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
            res = super(HrLoan, self).create(values)
            return res

    @api.multi
    def write(self, values):
        # print(values)
        today = datetime.today().strftime('%Y-%m-%d')
        today_date = datetime.strptime(today, '%Y-%m-%d')
        next_year = int(today_date.year) + 1
        fin_string = str(next_year) + "-03-31"
        date_march = datetime.strptime(fin_string, '%Y-%m-%d')

        if 'sureties_lines' in values:
            if len(values['sureties_lines']) > 2:
                raise ValidationError('You cannot add more than 2 Sureties.')

            # for line in values['sureties_lines']:
            #     for i in line:
            #         print("line", i)

        if not 'loan_lines' in values:
            values['installment_bool'] = False

        if 'payment_date' in values:
            if values['payment_date'] < today:
                raise ValidationError('You cannot make loan request for past dates.')

            payment_date = datetime.strptime(values['payment_date'], '%Y-%m-%d')
            if payment_date > date_march:
                raise ValidationError('You cannot make loan request for next financial years.')

        res = super(HrLoan, self).write(values)
        return res

    @api.onchange('employee_ref')
    def onchange_employee_ref(self):
        for record in self:
            if record.employee_ref:
                record.employee_id = self.env['hr.employee'].search([('emp_id', '=', record.employee_ref)])

    @api.onchange('employee_id')
    def onchange_employee_id_value(self):
        for record in self:
            if record.employee_id:
                record.employee_ref = record.employee_id.emp_id

    @api.onchange('loan_type')
    def onchange_loan_type(self):
        self.loan_percent = self.env['loan.interest'].search([('name', '=', self.loan_type)]).percentage
        return

    @api.multi
    def action_submit(self):
        if self.loan_type == 'short_term':
            if self.loan_amount > 0.0:
                start_date = datetime.strptime(self.date, "%Y-%m-%d")
                e_date = self.employee_id.date_of_joining
                end_date = datetime.strptime(e_date, "%Y-%m-%d" )
                years = relativedelta(start_date, end_date).years
                loan_amount = (2 * self.employee_id.gross_salary)
                if years >= 1:
                    if self.loan_amount <= loan_amount:
                        self.write({'state': 'waiting_approval_1'})
                    else:
                        raise ValidationError("For short term loan, You cannot make loan request for 2 times more than your Gross Salary")
                else:
                    raise ValidationError("For short term loan, You must have a minimum of 1 year continued service for this Company.")

            else:
                raise ValidationError("Loan amount should not be 0.")

        if self.loan_type == 'long_term':
            if self.loan_amount > 0.0:
                start_date = datetime.strptime(self.date, "%Y-%m-%d")
                e_date = self.employee_id.date_of_joining
                end_date = datetime.strptime(e_date, "%Y-%m-%d")
                years = relativedelta(start_date, end_date).years
                loan_amount = (5 * self.employee_id.gross_salary)
                if years >= 2:
                    if self.loan_amount <= loan_amount:
                        self.write({'state': 'waiting_approval_1'})
                    else:
                        raise ValidationError("For long term loan, You cannot make loan request for 5 times more than your Gross Salary")
                else:
                    raise ValidationError("For long term loan, You must have a minimum of 2 year continued service for this Company.")
            else:
                raise ValidationError("Loan amount should not be 0.")
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def action_approve(self):
        # for data in self:
            # if not data.loan_lines:
            #     raise ValidationError('Please Compute installment')
            # else:
        self.write({'state': 'approve', 'payment_date': fields.Date.today()})

    @api.multi
    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for loan in self:
            installment = ''
            if not loan.loan_lines:
                date_start = datetime.strptime(loan.payment_date, '%Y-%m-%d')
                if self.loan_type == 'short_term':
                    installment = int(self.short_term_installment)
                else:
                    installment = int(self.long_term_installment)
                amount = ((loan.loan_amount + ((loan.loan_amount * loan.loan_percent) / 100)) / installment)
                for i in range(1, installment + 1):
                    date_start = date_start + relativedelta(months=1)
                    self.env['hr.loan.line'].create({
                        'date': date_start,
                        'amount': amount,
                        'employee_id': loan.employee_id.id,
                        'loan_id': loan.id})
                self.write({'installment_bool': True})
        return True


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    amount = fields.Float(string="Amount", required=True)
    paid = fields.Boolean(string="Paid")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.")


class LoanSuretiesLines(models.Model):
    _name = "loan.sureties.lines"
    _description = "Surety Information"

    loan_id = fields.Many2one('hr.loan', string="Loan Ref.")
    employee_id = fields.Many2one('hr.employee', 'Employee')
    employee_ref = fields.Char(string="Employee ID", related="employee_id.emp_id")
    category_id = fields.Many2one('pappaya.employee.category', related="employee_id.category_id", string='Category', readonly=True)
    sub_category_id = fields.Many2one('hr.employee.subcategory', related="employee_id.sub_category_id", string='Sub Category', readonly=True)
    date_of_joining = fields.Date(string='Date of Join', related="employee_id.date_of_joining", readonly=True)
    gross_salary = fields.Float('Gross Salary(Per Month)', related="employee_id.gross_salary", readonly=True)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True, string="Department")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.one
    def _compute_employee_loans(self):
        for record in self:
            record.loan_count = record.env['hr.loan'].search_count([('employee_id', '=', record.id)])

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')
