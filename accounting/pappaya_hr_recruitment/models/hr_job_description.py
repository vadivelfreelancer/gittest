# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,timedelta


class PappayaJobDescriptionJD(models.Model):
    _name = 'pappaya.job.description'

    name = fields.Char('Name',size=100)
    description = fields.Text('Description', size=200)
    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    job_id = fields.Many2one('hr.job', string='Designation')
    subject_ids = fields.Many2many('pappaya.subject', string='Subjects')
    department_id = fields.Many2one('hr.department', string='Department')
    year_of_experience = fields.Integer(string='Years of experience')
    initial_date = fields.Date('Initial Date')
    last_date = fields.Date('Last Date', compute='compute_last_date')
    educational_qualification_ids = fields.Many2many('hr.recruitment.degree', string='Educational Qualifications')
    expected_date_of_joining = fields.Date(string='Expected Date Of Joining')
    budgeted_salary = fields.Integer(string="Salary Range (Gross per month)")
    preferred_skills = fields.Text(string="Preferred  Skills",size=300)
    desired_skills = fields.Text(string="Desired Skills ",size=200)
    no_of_recruitment = fields.Integer(string='Expected New Employees', default=0)
    state = fields.Selection([('draft', 'Draft'), ('request', 'Request'), ('confirm', 'Confirm'),('cancel','Cancel')], default='draft', string='Status')
    requisition_form_id = fields.Many2one('requisition.form',string='Requisition')

    
    @api.onchange('branch_id')
    def onchange_branch_id(self):
        self.department_id = None
        job_positions = self.env['hr.job'].search([('office_type_id', '=', self.branch_id.office_type_id.id)])
        department = []
        for job in job_positions:
            department.append(job.department_id.id)
        return {'domain': {'department_id': [('id', 'in', department)]}}
    
    @api.depends('initial_date')
    def compute_last_date(self):
        for record in self:
            if record.initial_date:
                last_date = datetime.strptime(record.initial_date, "%Y-%m-%d").date() + timedelta(days=15)
                record.last_date = last_date
    
    
    @api.multi
    def to_request(self):
        for record in self:
            last_date = datetime.strptime(record.initial_date, "%Y-%m-%d").date() + timedelta(days=15)
            if last_date >= datetime.today().date(): 
                record.state = 'request'
            else:
                raise ValidationError(_("Job Description is allowed to create on or before %s") %(last_date))

            
    @api.multi
    def to_confirm(self):
        for record in self:
            last_date = datetime.strptime(record.initial_date, "%Y-%m-%d").date() + timedelta(days=15)
            if last_date >= datetime.today().date(): 
                record.job_id.sudo().write({
                                        'no_of_recruitment':record.job_id.no_of_recruitment + record.no_of_recruitment,
                                        'budgeted_salary':record.budgeted_salary
                                        })
                exsit_job_vancancy = self.env['branch.wise.job.vecancy'].search([('branch_id','=',record.branch_id.id),('job_id','=',record.job_id.id)])
                if exsit_job_vancancy:
                    exsit_job_vancancy.write({
                                            'new_count': exsit_job_vancancy.new_count + record.no_of_recruitment,
                                            })
                else:
                    exsit_job_vancancy = self.env['branch.wise.job.vecancy'].create({
                                                                                    'branch_id' :   record.branch_id.id,
                                                                                    'job_id'    :   record.job_id.id,
                                                                                    'new_count' :   record.no_of_recruitment,  
                                                                                    })
                record.state = 'confirm'
            else:
                raise ValidationError(_("Job Description is allowed to Confirm on or before %s") %(last_date))
            
    
    @api.multi
    def to_cancel(self):
        for record in self:
            record.state = 'cancel'        
    
