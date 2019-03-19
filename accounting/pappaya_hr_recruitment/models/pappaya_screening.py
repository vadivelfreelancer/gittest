# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date
import math

class PappayaScreening(models.Model):
    _name = "pappaya.screening"
    _inherit = ['mail.thread']
    _rec_name = "branch_id"

    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    department_id = fields.Many2one('hr.department', string='Department')
    designation_id = fields.Many2one('hr.job', string='Designation')
    edu_qualification_ids = fields.Many2many('hr.recruitment.degree', string='Educational Qualification')
    application_ids = fields.Many2many('hr.applicant', string='Application')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft',string='State')

    @api.onchange('department_id','designation_id','edu_qualification_ids')
    def get_application_details(self):
        for record in self:
            applicant_val = self.env['hr.applicant'].search([
                                                            ('company_id','=',record.company_id.id),
                                                            ('branch_id','=',record.branch_id.id),
                                                             ('department_id','=',record.department_id.id),
                                                             ('job_id','=',record.designation_id.id),
                                                             ('type_id','in',record.edu_qualification_ids.ids),
                                                             ('short_list', '!=', True)
                                                             ])
            record.application_ids = applicant_val

    
    @api.onchange('branch_id')
    def onchange_branch_id(self):
        department = []
        if self.branch_id:
            self.department_id = None
            job_positions = self.env['hr.job'].search([('office_type_id','=',self.branch_id.office_type_id.id)])
            for job in job_positions:
                department.append(job.department_id.id)
        return {'domain':{'department_id':[('id','in',department)]}}
# 
    @api.onchange('department_id')
    def onchnage_department_id(self):
        for record in self:
            job_ids = []
            record.designation_id = None
            if record.department_id and record.branch_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.branch_id.office_type_id.id),
                                                           ('department_id', '=', record.department_id.id)
                                                           ])
                for job in job_positions:
                    job_ids.append(job.id)
            return {'domain': {'designation_id': [('id', 'in', job_ids)]}}

    def action_confirm_screening(self):
        for record in self:
            for application in record.application_ids:
                if application.screening_list:
                    application.short_list = True
            record.state = 'confirm'
