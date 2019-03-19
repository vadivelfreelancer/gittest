# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError, except_orm
import math


class HrAdvance(models.Model):
    _name = 'hr.advance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Advance Request"


    @api.onchange('emp_id')
    def onchange_emp_id(self):
        for record in self:
            if record.emp_id:
                employee = self.env['hr.employee'].search([('emp_id', '=', record.emp_id), ('active', '=', True)])
                if employee.employee_type.is_permanent == True:
                    record.employee_id = employee.id
                else:
                    raise ValidationError("Only Permanent Employees are eligible for Salary Advances.")

    @api.constrains('emp_id')
    def validate_emp_id(self):
        for record in self:
            if record.emp_id:
                employee = self.env['hr.employee'].search([('emp_id', '=', record.emp_id), ('active', '=', True)])
                if employee.employee_type.is_permanent != True:
                    raise ValidationError("Only Permanent Employees are eligible for Salary Advances.")

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for record in self:
            if record.employee_id:
                record.emp_id = record.employee_id.emp_id
            else:
                record.emp_id = None

    @api.constrains('requested_amount')
    def check_requested_amount(self):
        for advance in self:
            lastdate = (datetime.now() + relativedelta(day=1, days=-1)).strftime("%Y-%m-%d")
            firstdate = (datetime.now() + relativedelta(months=-1, day=1)).strftime("%Y-%m-%d")

            advance_count = self.env['hr.advance'].search_count([('employee_id', '=', advance.employee_id.id), ('state', '=', 'approve'), \
                                                                ('branch_id', '=', advance.branch_id.id), ('fiscal_year_id', '=', advance.fiscal_year_id.id)])
            if advance_count:
                raise ValidationError('The employee has already applied for Advance in this Fiscal Year')
            
#             last_payslip = self.env['hr.payslip'].search([('employee_id', '=', advance.employee_id.id), ('date_from', '=', firstdate), ('date_to', '=', lastdate),('company_id', '=', advance.branch_id.id)],order='id desc', limit=1)
#             if last_payslip.ids == []:
#                 raise ValidationError("Previous Month Payslip is not generated for this employee")
#             last_payslip_net_amt = 0
#             for rule in last_payslip.line_ids:
#                 if rule.code == 'GROSS':
#                     last_payslip_net_amt = rule.total
            net_amt = math.ceil(advance.employee_id.gross_salary * 0.50)
            if net_amt < advance.requested_amount:
                raise ValidationError(_("You are eligible only for Rs. %s as Salary Advance")%(net_amt))
            if advance.requested_amount <= 0:
                raise ValidationError("Requested amount should be greater than 'Zero' ")


    @api.depends('max_net_percent','requested_amount')
    def _compute_advance_amount(self):
        for advance in self:
            last_payslip_net_amt = 0.0

            lastdate = (datetime.now() + relativedelta(day=1, days=-1)).strftime("%Y-%m-%d")
            firstdate = (datetime.now() + relativedelta(months=-1, day=1)).strftime("%Y-%m-%d")

#             last_payslip = self.env['hr.payslip'].search([('employee_id', '=', advance.employee_id.id),('date_from', '=', firstdate), ('date_to', '=', lastdate),('company_id', '=', advance.branch_id.id)],order='id desc', limit=1)
#             for rule in last_payslip.line_ids:
#                 if rule.code == 'GROSS':
#                     last_payslip_net_amt = rule.total
    
            last_payslip_net_amt = advance.employee_id.gross_salary
            advance.last_payslip_net_amt = advance.employee_id.gross_salary
            net_amt = math.ceil(advance.employee_id.gross_salary * 0.50)

            if net_amt >= advance.requested_amount:
                advance.advance_amount = advance.requested_amount
            else:
                if last_payslip_net_amt > 0.0:
                    advance.advance_amount = math.ceil((advance.max_net_percent / 100) * last_payslip_net_amt)


    name = fields.Char(string="Name", readonly=True,size=100)
    date = fields.Date(string="Date", default=fields.Date.today())
    fiscal_year_id = fields.Many2one('fiscal.year', 'Fiscal Year', default=lambda self: self.env['fiscal.year'].search([('active', '=', True)]))
    emp_id = fields.Char('Employee ID',size=100)
    employee_id = fields.Many2one('hr.employee', string="Employee", domain=[('employee_type.name','=','Permanent')])
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True, string="Department")
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Designation")
    branch_id = fields.Many2one('res.company', string='Branch', related="employee_id.company_id", readonly=True)
    requested_amount = fields.Float(string="Requested Amount", required=True,size=8)
    max_net_percent = fields.Float(string="Advance (Max. Net %)", default=50.0)
    state = fields.Selection([('draft', 'Draft'), ('request', 'Requested'), ('approve', 'Approved'),  ('cancel', 'Cancelled')]
                                ,string="State", default='draft', track_visibility='onchange', copy=False)
    last_payslip_net_amt = fields.Float(string="Previous GROSS Amount", readonly=True, compute='_compute_advance_amount')
    advance_amount = fields.Float(string="Advance Amount", readonly=True, compute='_compute_advance_amount')
    is_recoverable = fields.Boolean('Is Recoverable', default=True)
    amount_deduct_payslip_id = fields.Many2one('hr.payslip', string='Payslip')
    payment_state   = fields.Selection([('pending','Pending'),('paid','Paid')],default='pending',string='Payment Status')

    @api.model
    def create(self, values):
        res = super(HrAdvance, self).create(values)
        sequence = self.env['ir.sequence'].search([('code', '=', 'hr.advance.seq')])
        res['name'] = sequence.get_id(sequence.id, 'id') or ' '
        return res

    @api.constrains('employee_id','state','branch_id','fiscal_year_id')
    def validation_employee_state_branch(self):
        for record in self:
            if len(record.search([('employee_id', '=', record.employee_id.id), ('state', '=', 'approve'), \
                                        ('branch_id', '=', record.branch_id.id), ('fiscal_year_id', '=', record.fiscal_year_id.id)])) > 1:
                raise ValidationError('The employee has already applied for Advance in this Fiscal Year')
            
    @api.onchange('requested_amount')
    @api.constrains('requested_amount')
    def onchange_requested_amount(self):
        if self.requested_amount and len(str(self.requested_amount)) > 8:
            self.requested_amount = 0.0
            return {
                    'warning': {'title': _('User Error'), 'message': _('Invalid Amount!'),},
                    }

    @api.multi
    @api.constrains('max_net_percent')
    def validation_max_net_percent(self):
        if self.max_net_percent > 50.0:
            raise ValidationError("Max. Net should not exceed 50%")

    @api.multi
    def action_submit(self):
        self.write({'state': 'request'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def action_approve(self):
        self.write({'state': 'approve'})

    @api.one
    def copy(self, default=None):
        raise ValidationError("You are not allowed to Duplicate")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.one
    def _compute_employee_advances(self):
        """This compute the advance amount and total advances count of an employee.
            """
        for record in self:
            record.advance_count = record.env['hr.advance'].search_count([('employee_id', '=', record.id)])

    advance_count = fields.Integer(string="Advance Count", compute='_compute_employee_advances')
