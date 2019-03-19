from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import babel
import xlsxwriter
import base64
import csv
import os

    
class PayrollRelease(models.Model):
    _name = 'payment.release'
    _inherit = 'mail.thread'
    _order = "id desc"
    _rec_name = 'month_id'

    date_start              = fields.Date(string='Date From')
    date_end                = fields.Date(string='Date To')
    region_ids              = fields.Many2many('pappaya.region','pappaya_region_release_rel','region_id','release_id',string="Region")
    state_ids               = fields.Many2many('res.country.state','res_country_state_release_rel','state_id','release_id',string="State",domain=[('country_id.is_active','=',True)])
    district_ids            = fields.Many2many("state.district", 'state_district_release_rel','state_id','release_id',string='District')
    office_type_ids         = fields.Many2many('pappaya.office.type','office_type_release_rel','state_id','release_id',string="Office Type")
    branch_ids              = fields.Many2many('operating.unit', 'branch_release_rel','branch_id','release_id',string='Branch',domain=[('type','=','branch')])
    department_ids          = fields.Many2many('hr.department','hr_department_release_rel','department_id','release_id',string='Department' )
    designation_ids         = fields.Many2many('hr.job','hr_job_release_rel','job_id','release_id',string='Designation' )
    salary_range            = fields.Float('Salary Range')
    operators               = fields.Selection([('=','='),('!=','!='),('>','>'),('>=','>='),('<','<'),('<=','<=')])
    state                   = fields.Selection([('draft', 'Draft'), ('request', 'Requested'), ('verified', 'Verified')]
                                , string="Status", default='draft', track_visibility='onchange', copy=False)
    hr_payslip_ids          = fields.Many2many('hr.payslip','hr_payslip_payment_release_rel','payslip_id','payment_id',string="Payslips")
    month_id                = fields.Many2one('calendar.generation.line',string='Month')
    
    # - REmove fields start
    region_id = fields.Many2one('pappaya.region')
    state_id = fields.Many2one('res.country.state',domain=[('country_id.is_active','=',True)])
    district_id = fields.Many2one('state.district')
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    office_type_id = fields.Many2one('pappaya.office.type',string="Office Type")
    department_id = fields.Many2one('hr.department')
    designation_id = fields.Many2one('hr.job')
    # remove fields end
    
    @api.constrains('salary_range')
    def check_salary_range(self):
        for record in self:
            if record.salary_range and record.salary_range < 0:
                raise ValidationError("Salary Range should not be Negative")
            
    @api.constrains('hr_payslip_ids')
    def check_hr_payslip_ids(self):
        for record in self:
            if not record.hr_payslip_ids.ids:
                raise ValidationError("Pay slips is Empty")
            self.env.cr.execute(""" select branch_id from hr_payslip where id in %s group by branch_id;""",(tuple(record.hr_payslip_ids.ids),))
            payslip_run_ids = self.env.cr.fetchall()
            payslip_run_ids_list = []
            for branch in payslip_run_ids:
                if branch:
                    employee_lock_sublock_sr = self.env['employee.lock.sublock'].sudo().search([('branch_id','=', branch[0]),
                                                                                         ('date_start','=',record.date_start),
                                                                                         ('date_end','=',record.date_end),
                                                                                         ('lock_state','=','approved'),
                                                                                         ('sublock_state','=','approved')
                                                                                         ])
                    if not employee_lock_sublock_sr:
                        raise ValidationError(_("You must create or approve Lock/Sublock - branch : %s") %(self.env['operating.unit'].browse(branch[0]).name))
                    

    @api.onchange('month_id')
    def onchange_month_id(self):
        for record in self:
            if record.month_id:
                record.date_start   = record.month_id.date_start
                record.date_end     = record.month_id.date_end

                
    @api.onchange('region_ids')
    def onchange_region_id(self):
        for record in self:
            domain = []
            region_domain = []
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
                state_ids = []
                for region_id in record.region_ids:
                    state_ids += region_id.state_id.ids
                region_domain.append(('id', 'in', state_ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
            domain.append(('type','=','branch'))
            return {'domain': {'state_ids': region_domain,'branch_ids': domain}}
    
    @api.onchange('state_ids')
    def onchange_state_id(self):
        for record in self:
            domain = []
            state_domain = []
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
                state_domain.append(('state_id', 'in', record.state_ids.ids))
            domain.append(('type','=','branch'))
            return {'domain': {'district_ids': state_domain,'branch_ids': domain}}
            
            
    @api.onchange('district_ids')
    def onchange_district_id(self):
        for record in self:
            domain = []
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            domain.append(('type','=','branch'))
            return {'domain': {'branch_ids': domain}}
    
    
    @api.onchange('office_type_ids')
    def onchange_office_type_id(self):
        for record in self:
            domain = []
            if record.state_ids:
                domain.append(('state_id','in',record.state_ids.ids))
            if record.region_ids:
                domain.append(('region_id','in',record.region_ids.ids))
            if record.district_ids:
                domain.append(('district_id','in',record.district_ids.ids))
            if record.office_type_ids:
                domain.append(('office_type_id','in',record.office_type_ids.ids))
            domain.append(('type','=','branch'))
            return {'domain': {'branch_ids': domain}}
                
    
    
    @api.onchange('date_start','date_end','region_ids','state_ids','branch_ids','district_ids','department_ids','designation_ids','salary_range','operators')
    def payslip_verification_onchnage(self):
        for record in self:
            if record.date_start and record.date_end:
                domain = []
                if record.state_ids:
                    domain.append(('state_id','in',record.state_ids.ids))
                if record.region_ids:
                    domain.append(('region_id','in',record.region_ids.ids))
                if record.district_ids:
                    domain.append(('district_id','in',record.district_ids.ids))
                if record.office_type_ids:
                    domain.append(('office_type_id','in',record.office_type_ids.ids))
                if record.branch_ids:
                    domain.append(('id','in',record.branch_ids.ids))
                domain.append(('type','=','branch'))
                branch_domain = self.env['operating.unit'].sudo().search(domain)
                
                lock_and_sublock_sr        =   self.env['employee.lock.sublock'].sudo().search([
                                                                                             ('branch_id','in',branch_domain.ids),
                                                                                             ('date_start','=',record.date_start),
                                                                                             ('date_end','=',record.date_end),
                                                                                             ('lock_state','=','approved'),
                                                                                             ('sublock_state','=','approved')
                                                                                            ])
                branch_ids = []
                for lock_and_sublock in lock_and_sublock_sr:
                    branch_ids.append(lock_and_sublock.branch_id.id)
                payslip_domain = []
                payslip_domain.append(('branch_id','in',branch_ids))
                if record.department_ids:
                    payslip_domain.append(('employee_id.department_id','in',record.department_ids.ids))
                if record.designation_id:
                    payslip_domain.append(('employee_id.job_id','in',record.designation_ids.ids))
                if record.date_start:
                    payslip_domain.append(('date_from','=',record.date_start))
                if record.date_end:
                    payslip_domain.append(('date_to','=',record.date_end))
                payslip_domain.append(('state','=','draft'))
                payslip_domain.append(('is_payroll_cycle','=',True))
                payslip_sr = self.env['hr.payslip'].search(payslip_domain,order="branch_id")
                if record.operators and record.salary_range:
                    slip_ids = []
                    for line in self.env['hr.payslip.line'].search([('slip_id','in',payslip_sr.ids),('code','=','NET'),('amount',record.operators,record.salary_range)]):
                        slip_ids.append(line.slip_id.id)
                    payslip_sr = self.env['hr.payslip'].search([('id','in',slip_ids)],order="branch_id")
                
                record.hr_payslip_ids = None
                if payslip_sr and payslip_sr.ids:
                    record.hr_payslip_ids = payslip_sr.ids
    
    
    @api.multi
    def payment_release(self):
        for record in self:
            for payslip in record.hr_payslip_ids:
                lock_and_sublock        =   self.env['employee.lock.sublock'].sudo().search([('payslip_batch_id','=',payslip.payslip_run_id.id),
                                                                                         ('branch_id','=',payslip.branch_id.id),
                                                                                         ('date_start','=',record.date_start),
                                                                                         ('date_end','=',record.date_end),
                                                                                         ('lock_state','=','approved'),
                                                                                         ('sublock_state','=','approved')
                                                                                         ])
                lock_and_sublock_line   =   self.env['employee.lock.sublock.line'].sudo().search([('lock_id','=',lock_and_sublock.id),
                                                                                                ('employee_id','=',payslip.employee_id.id),
                                                                                                ])
                if lock_and_sublock_line.is_lock or lock_and_sublock_line.is_sublock:
                    payslip.sudo().write({'is_lock':lock_and_sublock_line.is_lock,'is_sublock':lock_and_sublock_line.is_sublock})
                    if payslip.is_lock and payslip.is_sublock:
                        payslip.sudo().action_payslip_done_modification()
            record.state = 'verified'
                            
    @api.multi
    def action_submit(self):
        for record in self:
            record.state = 'request'
