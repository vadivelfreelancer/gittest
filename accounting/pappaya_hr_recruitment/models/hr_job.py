# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,timedelta


class HRJob(models.Model):
    _inherit='hr.job'
    
    
    year_of_experience = fields.Integer(string='Years of experience')
    expected_date_of_joining = fields.Date(string='Expected Date Of Joining')
    preferred_skills = fields.Text(string="Preferred  Skills" ,size=300)
    desired_skills = fields.Text(string="Desired Skills " ,size=200)
    educational_qualification = fields.Many2many('hr.recruitment.degree','hr_recruitment_degree_job_rel','job_id','degree_id',string='Educational Qualifications / Certifications')
    budgeted_salary = fields.Integer(string="Budgeted Salary (Per Month)")
    
    requisition_ids = fields.Many2many('requisition.form','requisition_form_job_rel','job_id','requisition_id',string='Requisition Form')
    salary_struct = fields.Many2one('hr.payroll.structure', string='Salary Structure')
    no_of_recruitment = fields.Integer(string='Expected New Employees', copy=False,
        help='Number of new employees you expect to recruit.', default=0)
    
    # JD Special fields
    job_description = fields.Boolean(string='Job Description')
    approve_state = fields.Selection([('draft','Draft'),('request','Request'),('confirm','Confirm')],default='draft')
    jd_initial_date = fields.Date('Initial Date')
    last_date = fields.Date('Last Date',compute='compute_last_date')
    new_no_of_recruitment = fields.Integer(string='Expected New Employees', copy=False,
        help='Number of new employees you expect to recruit.', default=0)

    @api.onchange('entity_id')
    def onchange_entity_id(self):
        for record in self:
            record.office_type_id = None
    
    @api.depends('jd_initial_date')
    def compute_last_date(self):
        for record in self:
            if record.jd_initial_date:
                last_date = datetime.strptime(record.jd_initial_date, "%Y-%m-%d").date() + timedelta(days=15)
                record.last_date = last_date
    
    
    @api.multi
    def to_request(self):
        for record in self:
            last_date = datetime.strptime(record.jd_initial_date, "%Y-%m-%d").date() + timedelta(days=15)
            if last_date >= datetime.today().date(): 
                record.approve_state = 'request'
            else:
                raise ValidationError(_("Job Description is allowed to create on or before %s") %last_date)
            
            
    @api.multi
    def to_confirm(self):
        for record in self:
            last_date = datetime.strptime(record.jd_initial_date, "%Y-%m-%d").date() + timedelta(days=15)
            if last_date >= datetime.today().date(): 
                record.approve_state = 'confirm'
            else:
                raise ValidationError(_("Job Description is allowed to create on or before %s") %last_date)


class UtmSource(models.Model):
    _inherit = 'utm.source'

    name = fields.Char(string='Source Name', required=True, translate=True,size=30)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name_lower = str(self.name.strip()).lower()
            name = self.env['res.company']._validate_name(name_lower)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name)]).ids) > 1:
            raise ValidationError("Source already exists")