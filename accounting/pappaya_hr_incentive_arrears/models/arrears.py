# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from odoo import tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
import re
import calendar


class HrArrears(models.Model):
    _name = 'hr.arrears'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _rec_name = 'name'

    name            = fields.Char('Arrear Sequence')
    date            = fields.Date(string="Date",default=lambda self:fields.Date.today())        
    from_month_id   = fields.Many2one('calendar.generation.line',string='From Month')
    to_month_id     = fields.Many2one('calendar.generation.line',string='To Month')
    branch_id       = fields.Many2one('operating.unit', 'Branch',domain=[('type','=','branch')])
    line_ids        = fields.One2many('hr.arrears.line','arrears_id',string="Arrears Line")
    state           = fields.Selection([('draft','Draft'),('request','Requested'),
                                    ('approve','Approved'),('cancel','Cancel')],default='draft',string='Status',track_visibility='onchange')
    payment_state   = fields.Selection([('pending','Pending'),('paid','Paid')],default='pending',string='Payment Status')
    
    @api.onchange('branch_id','from_month_id','to_month_id')
    def onchange_branch_from_to_month(self):
        for record in self:
            employee_list = []
            if record.from_month_id and record.to_month_id and record.branch_id:
                employees = self.env['hr.employee'].search([('branch_id','=',record.branch_id.id)])
                for employee in employees:
                    arrears_amt = 0.00
                    #employee_arrears_ids = []
                    employee_arrears = employee.gross_history_line.search([('id','in',employee.gross_history_line.ids),
                                                                           ('state','=','pending'),
                                                                           ('arrears_amt','>',0.00),
                                                                           '|',('date_start','>=',record.from_month_id.date_start),
                                                                           ('date_end','>=',record.from_month_id.date_end),
                                                                           ])
                    for arrears in employee_arrears:
                        arrears_amt += arrears.arrears_amt
                    if arrears_amt > 0.00:
                        employee_list.append((0,0,{
                                                'arrears_id'          : record.id,
                                                'from_month_id'       : record.from_month_id.id,
                                                'to_month_id'         : record.to_month_id.id,
                                                'date_from'           : record.from_month_id.date_start,
                                                'date_to'             : record.from_month_id.date_end,
                                                'employee_id'         : employee.id,
                                                'emp_id'              : employee.emp_id,
                                                'branch_id'           : employee.branch_id.id,
                                                'category_id'         : employee.category_id.id, 
                                                'sub_category_id'     : employee.sub_category_id.id,
                                                'department_id'       : employee.department_id.id,
                                                'designation_id'      : employee.job_id.id,
                                                'previous_salary_amt' : 0.00, 
                                                'current_salary_amt'  : employee.gross_salary,
                                                'proposed_amount'     : arrears_amt,
                                                'approved_amount'     : 0.00,
                                                'state'               : 'draft',
                                                'employee_gross_ids'  : [(6,0,employee_arrears.ids)]
                                                }))
            record.line_ids = None 
            record.line_ids = employee_list          

    @api.constrains('date')
    def date_constrains(self):
        for record in self:
            if datetime.strptime(record.date, "%Y-%m-%d").date() > datetime.today().date():
                raise ValidationError(_('Please avoid Future date %s')% record.date)
    
    @api.constrains('line_ids')
    def employee_invalid(self):
        for record in self:
            for line in record.line_ids:  
                employee_id = self.env['hr.employee'].search([('emp_id','=',line.emp_id),('branch_id','=',record.branch_id.id)])
                if not employee_id:
                    raise ValidationError(_('Employee (%s) not available, Please change Employee ID or Employee')% line.emp_id)
                if line.proposed_amount < 0.00:
                    raise ValidationError(_("Can't accept Proposed amount because amount is negative" ))
                if line.approved_amount < 0.00:
                    raise ValidationError(_("Can't Approved amount Amount because amount is negative" ))
            if not record.line_ids.ids:
                raise ValidationError(_("Can't save because employees list empty" ))
    
    @api.model
    def create(self,vals):
        res = super(HrArrears, self).create(vals)
        res.employee_invalid()
        sequence = self.env['ir.sequence'].search([('code', '=', 'arrear.sequence')])
        res['name'] = sequence.get_id(sequence.id, 'id') or ' '
        return res
    
    @api.multi
    def write(self,vals):
        res = super(HrArrears, self).write(vals)
        self.employee_invalid()
        return res

    @api.multi
    def to_request(self):
        for record in self:
            for line in record.line_ids:
                if line.proposed_amount == 0.00:
                    raise ValidationError(_("Can't accept Proposed Amount because amount is zero" ))
            record.line_ids.write({'state':'request'})
            record.write({'state':'request'})
            
    @api.multi
    def to_approve(self):
        for record in self:
            for line in record.line_ids:
                if line.approved_amount == 0.00:
                    raise ValidationError(_("Can't accept Proposed Amount because amount is zero" ))
            record.line_ids.write({'state':'approve'})
            for employee_gross in record.line_ids:
                print (employee_gross,"sssssssssssssssssssss")
                employee_gross.employee_gross_ids.write({'state':'paid'})
            record.write({'state':'approve'})
            
    @api.multi
    def to_cancel(self):
        for record in self:
            record.line_ids.write({'state':'cancel'})
            record.write({'state':'cancel'})


class HrArrearsLine(models.Model):
    _name = 'hr.arrears.line'
    _rec_name = 'branch_id'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    
    arrears_id          = fields.Many2one('hr.arrears',string='Arrears')
    from_month_id       = fields.Many2one('calendar.generation.line',string='From Month')
    to_month_id         = fields.Many2one('calendar.generation.line',string='To Month')
    date_from           = fields.Date(string='From Date')
    date_to             = fields.Date(string='From To')
    employee_id         = fields.Many2one('hr.employee', string='Name')
    emp_id              = fields.Char(string='Employee ID',size=10)
    branch_id           = fields.Many2one('operating.unit',string='Branch',domain=[('type','=','branch')])
    category_id         = fields.Many2one('pappaya.employee.category', string='Category')
    sub_category_id     = fields.Many2one('hr.employee.subcategory', string='Sub Category')
    department_id       = fields.Many2one('hr.department',string='Department')
    designation_id      = fields.Many2one('hr.job',string='Designation')
    previous_salary_amt = fields.Float(string='Previous Salary Amount')
    current_salary_amt  = fields.Float(string='Current Salary Amount')
    proposed_amount     = fields.Float(string='Proposed Amount')
    approved_amount     = fields.Float(string='Approved Amount')
    employee_gross_ids  = fields.Many2many('hr.employee.gross.line')
    state               = fields.Selection([('draft','Draft'),('request','requested'),
                                    ('approve','Approved'),('cancel','Cancel')],default='draft',string='Status')
    
    @api.constrains('employee_id','emp_id')
    def employee_repeat_check(self):
        for record in self:
            if self.arrears_id.line_ids:
                if record.employee_id:
                    if len(self.search([('employee_id','=', record.employee_id.id),('id','in',self.arrears_id.line_ids.ids)])) > 1:
                        raise ValidationError(_('Employee(%s) already exists')% record.employee_id.name)
                if record.emp_id:
                    if len(self.search([('emp_id','=', record.emp_id),('id','in',self.arrears_id.line_ids.ids)])) > 1:
                        raise ValidationError(_('Employee ID(%s) already exists')% record.emp_id)
                    
    @api.onchange('employee_id','emp_id')
    def onchanage_employee_id(self):
        for record in self:
            if record.employee_id:
                record.from_month_id    = record.arrears_id.from_month_id.id
                record.to_month_id      = record.arrears_id.to_month_id.id
                record.date_from        = record.arrears_id.from_month_id.date_start
                record.date_to          = record.arrears_id.to_month_id.date_end
                record.branch_id        = record.arrears_id.branch_id.id
                record.category_id      = record.employee_id.category_id.id
                record.sub_category_id  = record.employee_id.sub_category_id.id
                record.department_id    = record.employee_id.department_id.id
                record.designation_id   = record.employee_id.job_id.id
                record.emp_id           = record.employee_id.emp_id
                
            if record.emp_id:
                employee_id = self.env['hr.employee'].search([('emp_id','=',record.emp_id),('branch_id','=',record.arrears_id.branch_id.id)])
                if employee_id:
                    record.from_month_id    = record.arrears_id.from_month_id.id
                    record.to_month_id      = record.arrears_id.to_month_id.id
                    record.date_from        = record.arrears_id.from_month_id.date_start
                    record.date_to          = record.arrears_id.to_month_id.date_end
                    record.branch_id        = record.arrears_id.branch_id.id
                    record.category_id      = employee_id.category_id.id
                    record.sub_category_id  = employee_id.sub_category_id.id
                    record.department_id    = employee_id.department_id.id
                    record.designation_id   = employee_id.job_id.id
                    record.employee_id      = employee_id.id