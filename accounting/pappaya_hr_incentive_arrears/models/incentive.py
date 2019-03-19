# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from odoo import tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
import re
import calendar


class HrIncentive(models.Model):
    _name = 'hr.incentive'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    _rec_name = 'name'

    name        = fields.Char('Incentive Sequence')
    date        = fields.Date(string="Date")        
    month_id    = fields.Many2one('calendar.generation.line',string='Month')
    branch_id   = fields.Many2one('operating.unit', 'Branch',domain=[('type','=','branch')])
    line_ids    = fields.One2many('hr.incentive.line','incentive_id',string="Incentive Line")
    state       = fields.Selection([('draft','Draft'),('request','Requested'),('approve','Approved'),('cancel','Cancel')],default='draft',string='Status',track_visibility='onchange')
    payment_state   = fields.Selection([('pending','Pending'),('paid','Paid')],default='pending',string='Payment Status')
    
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
        res = super(HrIncentive, self).create(vals)
        res.employee_invalid()
        sequence = self.env['ir.sequence'].search([('code', '=', 'incentive.sequence')])
        res['name'] = sequence.get_id(sequence.id, 'id') or ' '
        return res
    
    @api.multi
    def write(self,vals):
        res = super(HrIncentive, self).write(vals)
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
            record.write({'state':'approve'})
            
    @api.multi
    def to_cancel(self):
        for record in self:
            record.line_ids.write({'state':'cancel'})
            record.write({'state':'cancel'})
            

class HrIncentiveLine(models.Model):
    _name = 'hr.incentive.line'
    _rec_name = 'month_id'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    
    incentive_id    = fields.Many2one('hr.incentive',string='Incentive')
    month_id        = fields.Many2one('calendar.generation.line',string='Month')
    date_from       = fields.Date(string='From Date')
    date_to         = fields.Date(string='From To')
    employee_id     = fields.Many2one('hr.employee', string='Name')
    emp_id          = fields.Char(string='Employee ID',size=10)
    branch_id       = fields.Many2one('operating.unit',string='Branch',domain=[('type','=','branch')])
    category_id     = fields.Many2one('pappaya.employee.category', string='Category')
    sub_category_id = fields.Many2one('hr.employee.subcategory', string='Sub Category')
    department_id   = fields.Many2one('hr.department',string='Department')
    designation_id  = fields.Many2one('hr.job',string='Designation')
    proposed_amount = fields.Float(string='Proposed Amount')
    approved_amount = fields.Float(string='Approved Amount')
    state           = fields.Selection([('draft','Draft'),('request','requested'),
                                    ('approve','Approved'),('cancel','Cancel')],default='draft',string='Status')
    
    
    @api.constrains('employee_id','emp_id')
    def employee_repeat_check(self):
        for record in self:
            if self.incentive_id.line_ids:
                if record.employee_id:
                    if len(self.search([('employee_id','=', record.employee_id.id),('id','in',self.incentive_id.line_ids.ids)])) > 1:
                        raise ValidationError(_('Employee(%s) already exists')% record.employee_id.name)
                if record.emp_id:
                    if len(self.search([('emp_id','=', record.emp_id),('id','in',self.incentive_id.line_ids.ids)])) > 1:
                        raise ValidationError(_('Employee ID(%s) already exists')% record.emp_id)

    @api.onchange('employee_id','emp_id')
    def onchanage_employee_id(self):
        for record in self:
            if record.employee_id:
                record.month_id         = record.incentive_id.month_id.id
                record.date_from        = record.incentive_id.month_id.date_start
                record.date_to          = record.incentive_id.month_id.date_end
                record.branch_id        = record.incentive_id.branch_id.id
                record.category_id      = record.employee_id.category_id.id
                record.sub_category_id  = record.employee_id.sub_category_id.id
                record.department_id    = record.employee_id.department_id.id
                record.designation_id   = record.employee_id.job_id.id
                record.emp_id           = record.employee_id.emp_id
                
            if record.emp_id:
                employee_id = self.env['hr.employee'].search([('emp_id','=',record.emp_id),('branch_id','=',record.incentive_id.branch_id.id)])
                if employee_id:
                    record.month_id         = record.incentive_id.month_id.id
                    record.date_from        = record.incentive_id.month_id.date_start
                    record.date_to          = record.incentive_id.month_id.date_end
                    record.branch_id        = record.incentive_id.branch_id.id
                    record.category_id      = employee_id.category_id.id
                    record.sub_category_id  = employee_id.sub_category_id.id
                    record.department_id    = employee_id.department_id.id
                    record.designation_id   = employee_id.job_id.id
                    record.employee_id      = employee_id.id