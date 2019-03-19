#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import babel
from odoo import models, fields, api, tools, _
from odoo.exceptions import Warning
from dateutil.relativedelta import relativedelta
from datetime import date
from datetime import datetime
from openerp.exceptions import UserError, AccessError, ValidationError
from openerp.tools.translate import _
from dateutil import parser
from odoo.tools import float_compare, float_is_zero
import calendar
# from odoo.fields import Many2one
# from cobble import field

class HrSalaryRuleExitLine(models.Model):
    _name='hr.salary.rule.exit.line'
    
    name = fields.Many2one('hr.salary.rule', 'Name')
    code = fields.Char('Code', related='name.code')
    
    amount = fields.Float('Amount')
    exit_id = fields.Many2one('hr.exit','Exit Id')    




class hr_exit(models.Model):
    _name = 'hr.exit'
    _description = "Exit"
    _rec_name = 'employee_id'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for record in self:
            if record.employee_id:
                employee_asset_sr = self.env['employee.asset.allocation'].search([('employee_id','=',record.employee_id.id)])
                if employee_asset_sr:
                    record.asset_ids = [(6, 0,employee_asset_sr.ids)]

    @api.onchange('emp_id')
    def onchange_emp_id(self):
        for record in self:
            if record.emp_id:
                employee = self.env['hr.employee'].search([('emp_id', '=', record.emp_id), ('active', '=', True)])
                if employee:
                    record.employee_id = employee.id
                else:
                    record.employee_id = None

    
    employee_id = fields.Many2one('hr.employee', string="Employee")
    emp_id = fields.Char(string='Employee ID', size=6)
    request_date = fields.Date('Request Date',
                    default=fields.datetime.now())
    user_id = fields.Many2one('res.users', string='User', 
                        default=lambda self: self.env.user, 
                        states={'draft':[('readonly', False)]}, readonly=True)
    confirm_date = fields.Date(string='Confirm Date(Employee)',readonly=True, copy=False)
    dept_approved_date = fields.Date(string='Approved Date(Department Manager)',readonly=True, copy=False)
    validate_date = fields.Date(string='Approved Date(HR Manager)',readonly=True, copy=False)
    general_validate_date = fields.Date(string='Approved Date(General Manager)',readonly=True, copy=False)
    confirm_by_id = fields.Many2one('res.users', string='Confirm By',readonly=True, copy=False)
    dept_manager_by_id = fields.Many2one('res.users', string='Approved By Department Manager',readonly=True, copy=False)
    hr_manager_by_id = fields.Many2one('res.users', string='Approved By HR Manager',readonly=True, copy=False)
    gen_man_by_id = fields.Many2one('res.users', string='Approved By General Manager',readonly=True, copy=False)
    reason_for_leaving = fields.Char(string='Reason For Leaving',required=True, copy=False, readonly=True,size=100)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    payment_state   = fields.Selection([('pending','Pending'),('paid','Paid')],default='pending',string='Payment Status')
    
    state = fields.Selection([('draft', 'Draft'), 
                        ('confirm', 'Requested'),
                        ('approved_dept_manager', 'Approved by Dept Manager'),
                        ('approved_hr_manager', 'Approved by HR Manager'),
                        ('approved_general_manager', 'Approved by General Manager'),
                        ('done', 'Done'),
                        ('cancel', 'Cancel'),
                        ('reject', 'Rejected')], string='State',
                        readonly=True, default='draft')              
    notes = fields.Text(string='Notes',size=300)
    wage = fields.Float(string='Basic', compute="compute_wage_basic")
    last_drawn_salary = fields.Float('Last Drawn Salary',compute="get_payslip")
    no_of_yrs = fields.Integer('No Of Years Completed',related='employee_id.no_of_yrs')
    gratuity = fields.Float('Gratuity',compute="gratuity_calculate")
    manager_id = fields.Many2one('hr.employee', 'Department Manager')
    department_id = fields.Many2one(related='employee_id.department_id', string='Department', type='many2one', readonly=True, store=True)
    job_id = fields.Many2one(related='employee_id.job_id',  string='Job Title', type='many2one', readonly=True, store=True)
    contract_id = fields.Many2one('hr.contract', string='Contract', readonly=False)
    contract_ids = fields.Many2many('hr.contract','hr_contract_contract_tag')
    line_ids = fields.One2many('hr.salary.rule.exit.line','exit_id', string='Salary Computation')
    
    salary_journal = fields.Many2one('account.journal', 'Salary Journal')
    slip_id = fields.Many2one('hr.payslip','Slip')
    asset_ids = fields.Many2many('employee.asset.allocation','asset_hr_exit_rel','asset_id','exit_id',string='hr_contract_contract_tag')
    #debit_account = fields.Many2one('account.account','Debit Account')
    #credit_account = fields.Many2one('account.account','Credit Account')
    
    @api.multi
    def compute_salary_calculation(self):
        for record in self:
            gratuity = record.gratuity
            record.line_ids = None
            date_start = datetime.strptime(record.date_from, "%Y-%m-%d").date()
            date_end = datetime.strptime(record.date_to, "%Y-%m-%d").date()
            hr_payslip_obj = self.env['hr.payslip']
            payslip = hr_payslip_obj.search([('employee_id','=',record.employee_id.id),('date_from','=',date_start),('date_to','=',date_end)])
            contract_id = self.env['hr.contract'].search([('employee_id','=',record.employee_id.id)],limit=1)
            payslip_run_id = self.env['hr.payslip.run'].search([('branch_id','=',record.employee_id.branch_id.id),
                                                                ('date_start','=',date_start),
                                                                ('date_end','=',date_end)
                                                                ],order="id desc",limit=1)
            
            if not payslip:
                payslips = self.env['hr.payslip']
                for employee in record.employee_id:
                    slip_data = self.env['hr.payslip'].onchange_employee_id(str(date_start), str(date_end), employee.id, contract_id=False)
                    res = {
                        'employee_id': employee.id,
                        'name': 'Employee Exit ' + slip_data['value'].get('name'),
                        'struct_id': slip_data['value'].get('struct_id'),
                        'contract_id': contract_id.id,
                        'date_from': date_start,
                        'date_to': date_end,
                        'company_id': employee.company_id.id,
                        'branch_id': employee.branch_id.id,
                        'exist_slip':True,
                        'payslip_run_id':payslip_run_id.id,
                        'number' : self.env['ir.sequence'].sudo().next_by_code('exit.salary.slip')
                    }
                    payslips = self.env['hr.payslip'].sudo().create(res)
                    
                    for payslip in payslips:
                        input_lines = []
                        contract_ids = payslip.contract_id.ids
                        work_hours = self.env['branch.officetype.workhours.line'].search([('branch_id','=',payslip.branch_id.id),('status_type','=','present')],limit=1)
                        
                        self.env.cr.execute(""" select create_payslip_lines(%s, %s, %s, %s, %s, %s,%s); """,
                                                        (payslip.employee_id.id,payslip.contract_id.id,payslip.branch_id.id,payslip.id,payslip.date_from,payslip.date_to,work_hours.min_work_hours))
                        input_lines.append((0,0,{
                                    'name': 'Gratuity',
                                    'sequence': 10,
                                    'code': 'GRA',
                                    'amount':gratuity,
                                    'contract_id': record.contract_id.id,
                                }
                                ))
                        payslip.sudo().input_line_ids =  input_lines
                        if payslip.line_ids:
                            self.env.cr.execute('delete from hr_payslip_line WHERE id in %s', (tuple(payslip.line_ids.ids),))
                        lines = [(0, 0, line) for line in payslip._get_payslip_lines(contract_ids, payslip.id)]
                        payslip.sudo().write({'line_ids': lines})
                        
                        line_data = []
                        record.line_ids = None
                        for line in payslip.line_ids:
                            line_data.append((0,0,{
                                                    'name':line.salary_rule_id.id,
                                                    'code':line.code,
                                                    'amount':line.total
                                                    }))
                        
                        record.line_ids = line_data
                        record.slip_id = payslip.id
            else:
                for payslip in payslip:
                    input_lines = []
                    contract_ids = payslip.contract_id.ids
                    work_hours = self.env['branch.officetype.workhours.line'].search([('branch_id','=',payslip.branch_id.id),('status_type','=','present')],limit=1)

                    self.env.cr.execute(""" select create_payslip_lines(%s, %s, %s, %s, %s, %s,%s); """,
                                                    (payslip.employee_id.id,payslip.contract_id.id,payslip.branch_id.id,payslip.id,payslip.date_from,payslip.date_to,work_hours.min_work_hours))
                    input_lines.append((0,0,{
                                'name': 'Gratuity',
                                'sequence': 10,
                                'code': 'GRA',
                                'amount':gratuity,
                                'contract_id': record.contract_id.id,
                            }
                            ))
                    payslip.sudo().input_line_ids =  input_lines
                    if payslip.line_ids:
                        self.env.cr.execute('delete from hr_payslip_line WHERE id in %s', (tuple(payslip.line_ids.ids),))
                    lines = [(0, 0, line) for line in payslip._get_payslip_lines(contract_ids, payslip.id)]
                    payslip.sudo().write({'line_ids': lines})

                    line_data = []
                    record.line_ids = None
                    for line in payslip.line_ids:
                        line_data.append((0,0,{
                                                'name':line.salary_rule_id.id,
                                                'code':line.code,
                                                'amount':line.total
                                                }))

                record.line_ids = line_data
                record.slip_id = payslip.id
                
    
    
    @api.depends('wage','employee_id')
    def compute_wage_basic(self):
        for record in self:
            record.wage = record.contract_id.wage
    @api.one
    @api.depends('last_drawn_salary','employee_id')
    def get_payslip(self):
        payslip_obj = []
        if self.slip_id:
            payslip_obj = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id),('id','!=',self.slip_id.id)], order = "id desc")
        else:
            payslip_obj = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id)], order = "id desc")
        if payslip_obj:
            for pay in payslip_obj[0].line_ids:
                if pay.code=='BASIC':
                    self.last_drawn_salary = pay.amount
    @api.one
    @api.depends('gratuity','employee_id')
    def gratuity_calculate(self):
        if self.no_of_yrs >= 3:
            self.gratuity = round((float(15 / 26) * self.last_drawn_salary * float(self.no_of_yrs)))
        else:
            self.gratuity = 0.00

    @api.constrains('line_ids')
    def check_line_ids(self):
        ff_values = []
        for record in self:
            for line in record.line_ids:
                if line.name.id not in ff_values:
                    ff_values.append(line.name.id)
                else:
                    raise ValidationError('Check the Salary Heads in Full & Final Settlement. Some Salary Heads are repetitive !!')
    
    
    @api.one
    def get_contract_latest(self, employee, date_from, date_to):
        """
        @param employee: browse record of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        contract_obj = self.env['hr.contract']
        clause = []
        #a contract is valid if it ends between the given dates
        clause_1 = ['&',('date_end', '<=', date_to),('date_end','>=', date_from)]
        #OR if it starts between the given dates
        clause_2 = ['&',('date_start', '<=', date_to),('date_start','>=', date_from)]
        #OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&',('date_start','<=', date_from),'|',('date_end', '=', False),('date_end','>=', date_to)]
        clause_final =  [('employee_id', '=', employee.id),'|','|'] + clause_1 + clause_2 + clause_3
        contract_ids = contract_obj.search(clause_final,limit=1)
        return contract_ids
    
    
    @api.depends('no_of_yrs','employee_id')
    def set_no_of_years(self):
        for rec in self:
            years = 0
            months = 0.00
            contract_ids = rec.contract_ids
            print (contract_ids,"contract_idscontract_idscontract_ids")
            for contract in contract_ids:
                if contract.date_start:
                    dt = contract.date_start
                    d1 = datetime.strptime(dt, "%Y-%m-%d").date()
                    d2 = None
                    if contract.date_end:
                        d2 = datetime.strptime(contract.date_end, "%Y-%m-%d").date()
                    else:
                        #d1 = datetime.strptime(dt, "%Y-%m-%d").date()
                        #d2 = date.today()
                        d2 = datetime.strptime(rec.request_date, "%Y-%m-%d").date()
                    rd = relativedelta(d2, d1)
                    #rec.age = str(rd.years) + ' years'
                    years +=  int(rd.years)
                    print (rd.years,rd.months,"11111111111111111")
                    months +=  rd.months
            rec.no_of_yrs = years + int(round(months/12))
            #rec.no_of_yrs_char = str(years) + ' Years' + ' - ' + str(int(round(months))) + ' Months'
            #return years 
    
    
    
    
    @api.onchange('employee_id', 'state')
    def get_contract(self):
        contract_obj = self.env['hr.contract']
        if self.employee_id:
            self.contract_id = contract_obj.search([('employee_id', '=', self.employee_id.id),('state','=','open')]).id
            self.contract_ids = contract_obj.search([('employee_id', '=', self.employee_id.id)]).ids
            return {'domain': {'contract_id': [('employee_id', '=', self.employee_id.id)],'contract_ids': [('employee_id', '=', self.employee_id.id)]}}
    
    @api.multi
    def exit_approved_by_department(self):
        obj_emp = self.env['hr.employee']
        self.state = 'confirm'
        self.dept_approved_date = time.strftime('%Y-%m-%d')

    @api.constrains('request_date', 'date_from','date_to')
    def check_request_last_work_date(self):
        for record in self:
            if (record.request_date < record.employee_id.date_of_joining) or (record.date_from < record.employee_id.date_of_joining) or (record.date_to < record.employee_id.date_of_joining):
                raise ValidationError('Request Date or Date From or Date To is less than Employee Joining Date !!')
    

    @api.multi
    def request_set(self):
        self.state = 'draft'
        
        
    @api.multi
    def exit_cancel(self):
        self.state = 'cancel'    
    
    
    @api.multi
    def get_confirm(self):
        self.state = 'confirm'
        self.confirm_date = time.strftime('%Y-%m-%d')
        self.confirm_by_id = self.env.user.id
    
    
    @api.multi
    def get_apprv_dept_manager(self):
        for record in self:
            for asset_line in record.asset_ids:
                if asset_line.state == 'allocate':
                    raise ValidationError(_('Please ensure all the asset are returned  "%s" ') % asset_line.asset_id.name)
            record.state = 'approved_dept_manager'
            record.dept_approved_date = time.strftime('%Y-%m-%d')
            record.dept_manager_by_id = self.env.user.id
    
    @api.multi
    def get_apprv_hr_manager(self):
        self.state = 'approved_hr_manager'
        self.validate_date = time.strftime('%Y-%m-%d')
        self.hr_manager_by_id = self.env.user.id
    
    
    @api.multi
    def get_apprv_general_manager(self):
        self.state = 'approved_general_manager'
        self.general_validate_date = time.strftime('%Y-%m-%d')
        self.gen_man_by_id = self.env.user.id
    
    @api.multi
    def get_done(self):
        timenow = time.strftime('%Y-%m-%d')
        self.sudo().state = 'done'
        self.employee_id.sudo().write({'active':False,'date_of_left':timenow})
        self.employee_id.user_id.sudo().write({'active':False})
        users = self.env['res.users'].search([('employee_id','=',self.employee_id.id)])
        users.write({'active':False})
        self.contract_id.sudo().write({'state':'close','date_end':timenow})
    
    @api.multi
    def get_reject(self):
        self.state = 'reject'
        
    @api.multi
    def print_slip(self):
        return self.env.ref('pappaya_payroll.report_payslip_inherit').report_action(self)
            

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    exist_slip = fields.Boolean('Exist Payslip',default=False)
       
    
class EmployeeAllocationLine(models.Model):
    _inherit = "employee.asset.allocation"
    
    
    @api.multi
    def return_asset(self):
        for record in self:
            if not record.returned_date :
                 raise ValidationError(_('Please given  Returned Date'))
            if record.returned_date and record.allocated_date:
                if record.returned_date < record.allocated_date:
                    raise ValidationError('Return Date is less than Asset Allocation Date !!')
            record.state = 'return'

    @api.constrains('allocated_date', 'returned_date')
    def check_allocated_returned_date(self):
        for record in self:
            if record.returned_date and record.allocated_date:
                if record.returned_date < record.allocated_date:
                    raise ValidationError('Return Date must be greater than Asset Allocation Date !!')

            doj = parser.parse(record.employee_id.date_of_joining)
            proper_doj = doj.strftime('%d-%m-%Y')

            if record.allocated_date:
                if record.allocated_date < record.employee_id.date_of_joining:
                    raise ValidationError(_("Allocated Date must be greater than Employee's Date of Joining %s ") % (proper_doj))

            if record.returned_date:
                if record.returned_date < record.employee_id.date_of_joining:
                    raise ValidationError(_("Return Date must be greater than Employee's Date of Joining %s ") % (proper_doj))
    