# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from odoo import tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
import re
import calendar


class BranchWiseRevised(models.Model):
    _name = 'branch.wise.revised'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _rec_name='date'
    
    date            = fields.Date(string='Date',default=lambda self:fields.Date.today())
    organization_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    entities_id     = fields.Many2one('operating.unit',string='Entities',domain=[('type','=','entity')])
    branch_state_id = fields.Many2one('res.country.state',string='State',domain=[('country_id.is_active','=',True)])
    office_type     = fields.Many2one('pappaya.office.type',string='Office Type')
    branch_id       = fields.Many2one('operating.unit', 'Branch',domain=[('type','=','branch')])
    category_id     = fields.Many2one('pappaya.employee.category', string='Category')
    sub_category_id = fields.Many2one('hr.employee.subcategory', string='Sub Category')
    department_id   = fields.Many2one('hr.department',string='Department')
    designation_id  = fields.Many2one('hr.job',string='Designation')
    month_id        = fields.Many2one('calendar.generation.line',string='Month')
    
    line_ids = fields.One2many('branch.wise.revised.line','branch_incre_id',string="Branch Wise")
    state = fields.Selection([('draft','Draft'),('request','Request'),('confirm','Confirm')],default='draft',string='Status')
    
    @api.constrains('date')
    def date_constrains(self):
        for record in self:
            if datetime.strptime(record.date, "%Y-%m-%d").date() > datetime.today().date():
                raise ValidationError(_('Please avoid Future date %s')% record.date)
    
    
    @api.onchange('branch_id')
    def onchange_branch_id(self):
        for record in self:
            if record.branch_id:
                category = []
                subcategory = []
                department = []
                designation = []
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.branch_id.office_type_id.id)])
                for job in job_positions:
                    category.append(job.category_id.id)
                    subcategory.append(job.sub_category_id.id)
                    department.append(job.department_id.id)
                    designation.append(job.id)
                return {'domain': {'category_id': [('id', 'in', category)],
                                   'sub_category_id': [('id', 'in', subcategory)],
                                   'department_id': [('id', 'in', department)],
                                   'designation_id': [('id', 'in', designation)],
                                   
                                   }}
                
    
    
    
    @api.onchange('category_id')
    def onchange_branch_category_id(self):
        for record in self:
            subcategory = []
            record.sub_category_id = None
            if record.branch_id and record.category_id:
                category = []
                subcategory = []
                department = []
                designation = []
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.branch_id.office_type_id.id),('category_id', '=', record.category_id.id)])
                for job in job_positions:
                    subcategory.append(job.sub_category_id.id)
                    department.append(job.department_id.id)
                    designation.append(job.id)
                return {'domain': {'sub_category_id': [('id', 'in', subcategory)],
                                   'department_id': [('id', 'in', department)],
                                   'designation_id': [('id', 'in', designation)],
                                   
                                   }} 
        
        
    @api.onchange('sub_category_id')
    def onchange_branch_subcategory_id(self):
        for record in self:
            department_ids = []
            designation = []
            record.department_id = record.job_id = None
            if record.category_id and record.branch_id and record.sub_category_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.branch_id.office_type_id.id),
                                                           ('category_id', '=', record.category_id.id),
                                                           ('sub_category_id', '=', record.sub_category_id.id)
                                                           ])
                for job in job_positions:
                    department_ids.append(job.department_id.id)
                    designation.append(job.id)
                return {'domain': {'department_id': [('id', 'in', department_ids)],
                                   'designation_id': [('id', 'in', designation)],
                                   }}
    
    
    @api.onchange('department_id')
    def onchnage_department_id(self):
        for record in self:
            job_ids = []
            record.job_id = None
            if record.department_id and record.branch_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.branch_id.office_type_id.id),
                                                           ('department_id', '=', record.department_id.id),
                                                           ('category_id', '=', record.category_id.id),
                                                           ('sub_category_id', '=', record.sub_category_id.id)
                                                           ])
                for job in job_positions:
                    job_ids.append(job.id)
                print (job_ids,"eeeeeeeeeeeeeeeeesswdedwdfeqqrfqeerfq")
                return {'domain': {'job_id': [('id', 'in', job_ids)]}}
    
    
    
    
    @api.onchange('month_id','sub_category_id','category_id','department_id','branch_id','designation_id')
    def onchange_date_branch_id(self):
        for record in self:
            if record.month_id and record.branch_id:
                domain = []
                if record.branch_id:
                    domain.append(('branch_id','=',record.branch_id.id))
                if record.category_id:
                    domain.append(('category_id','=',record.category_id.id))
                if record.sub_category_id:
                    domain.append(('sub_category_id','=',record.sub_category_id.id))
                if record.department_id:
                    domain.append(('department_id','=',record.department_id.id))
                if record.designation_id:
                    domain.append(('job_id','=',record.designation_id.id))
                    
                employee_sr = self.env['hr.employee'].search(domain,order='branch_id')
                line_list = []
                for employee in employee_sr:
                    line_list.append({
                                        'branch_incre_id'   : record.id, 
                                        'date'              : record.date,
                                        'employee_id'       : employee.id,
                                        'emp_no'            : employee.emp_id,
                                        'branch_id'         : employee.branch_id.id,
                                        'category_id'       : employee.category_id.id,
                                        'sub_category_id'   : employee.sub_category_id.id,
                                        'department_id'     : employee.department_id.id,
                                        'designation_id'    : employee.job_id.id,
                                        'effective_month'   : record.month_id.id,
                                        'existing_salary'   : employee.gross_salary,
                                        'increment_amt'     : 0.00,
                                        'arrears_amt'       : 0.00,
                                        'state'             : 'draft',
                                        })
                record.line_ids = []
                record.line_ids = line_list
                
    @api.multi
    def to_request(self):
        for record in self:
            record.state = 'request'
            
    @api.multi
    def to_confirm(self):
        for record in self:
            for line in record.line_ids:
                if line.new_salary:
                    old_gross = line.employee_id.gross_salary
                    line.employee_id.write({'gross_salary':line.new_salary,
                                            'gross_history_line':[(0, 0, {
                                                                    'date'          : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                                    'user_id'       : self.env.user.id,
                                                                    'old_gross'     : old_gross,
                                                                    'new_gross'     : line.new_salary,
                                                                    'update_reason' : 'Salary Increment',
                                                                    'employee_id'   : line.employee_id.id,
                                                                    'state'         : 'pending' if line.arrears_amt > 0.00 else 'non_pending',
                                                                    'arrears_amt'   : line.arrears_amt,
                                                                    'from_month_id' : line.effective_month.id,
                                                                    'to_month_id'   : record.month_id.id,
                                                                    'date_start'    : line.effective_month.date_start,
                                                                    'date_end'      : record.month_id.date_end,
                                                                    
                                                                    })]
                                            })
                line.state = 'done'
            record.state = 'confirm'
                            
class BranchWiseRevisedLine(models.Model):
    _name = 'branch.wise.revised.line'
    _rec_name = 'date'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    
    branch_incre_id             = fields.Many2one('branch.wise.revised',string='Branch Wise Revised')
    date                        = fields.Date(string='Date')
    employee_id                 = fields.Many2one('hr.employee', string='Name')
    emp_no                      = fields.Char(string='Employee ID',size=10)
    organization_id             = fields.Many2one('res.company',string='Organization',domain=[('type','=','organization')])
    branch_id                   = fields.Many2one('operating.unit',string='Branch',domain=[('type','=','branch')])
    category_id                 = fields.Many2one('pappaya.employee.category', string='Category')
    sub_category_id             = fields.Many2one('hr.employee.subcategory', string='Sub Category')
    department_id               = fields.Many2one('hr.department',string='Department')
    designation_id              = fields.Many2one('hr.job',string='Designation')
    existing_salary             = fields.Float(string='Existing salary')
    increment_amt               = fields.Float(string='Increment Amount')
    new_salary                  = fields.Float(string='New Salary',compute='new_salary_amt')
    arrears_amt                 = fields.Float(string='Arrears amount',compute='cal_arrears_amt')
    state                       = fields.Selection([('draft','Draft'),('done','Done')],default='draft',string='Status')
    effective_date              = fields.Date(string='Effective Date / Month')
    effective_month             = fields.Many2one('calendar.generation.line',string='Effective Month')
    
    @api.depends('existing_salary','increment_amt')
    def new_salary_amt(self):
        for record in self:
            if record.existing_salary and record.increment_amt:
                record.new_salary = abs(record.existing_salary + record.increment_amt)
                
                
    @api.depends('effective_month','new_salary','increment_amt')
    def cal_arrears_amt(self):
        for record in self:
            if record.increment_amt and  record.new_salary and record.existing_salary and record.effective_month and record.branch_incre_id.date:
                salary_change_date = datetime.strptime(record.branch_incre_id.month_id.date_end, "%Y-%m-%d").date()
                salary_change_effective_date = datetime.strptime(record.effective_month.date_end, "%Y-%m-%d").date()
                if salary_change_date >  salary_change_effective_date and salary_change_date.month != salary_change_effective_date.month:
                    rd = relativedelta(salary_change_date, salary_change_effective_date)
                    months =  rd.months
                    days = rd.days
                    arrears_amt = months*record.increment_amt
                    if arrears_amt > 0.00:
                        record.arrears_amt = arrears_amt
                else:
                    record.arrears_amt = 0.00
                     
