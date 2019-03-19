# -*- coding: utf-8 -*-

from openerp import models, fields, api,_
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError


class AttendanceRegister(models.Model):
    _name = 'pappaya.attendance.register'
    
    @api.model
    def _default_company(self):
        user_id=self.env['res.users'].browse(self.env.uid)
        return user_id.company_id
        
    @api.model
    def default_university(self):
        university_ids=self.env['pappaya.university'].search([('user_ids','in',self.env.uid)])
        if not university_ids:
            univer_ids1=self.env['res.users'].search([('id','=',self.env.uid)]).department_ids
            if univer_ids1:
                return univer_ids1[0].university_id[0]
            univer_ids=self.env['res.users'].search([('id','=',self.env.uid)]).faculty_ids
            if univer_ids:
                return univer_ids[0].university_id[0]
        return university_ids and university_ids[0] 
    
    @api.model
    def default_department(self):
        department_ids=self.env['pappaya.department'].search([('user_ids','in',self.env.uid)])
        return department_ids and department_ids[0] 
    
    
    name = fields.Char('Name', size=16, required=True)
    code = fields.Char('Code', size=8, required=True)
    company_id = fields.Many2one('res.company', 'Organisation',select=True,  default=_default_company )
    university_id = fields.Many2one('pappaya.university','Institution', default=default_university)
    department_id=fields.Many2one('pappaya.department','Department' ,default=default_department)
    course_id = fields.Many2one('pappaya.grade', 'Course', required=True)
    batch_id = fields.Many2one('pappaya.batch', 'Batch', required=True)
    subject_id = fields.Many2one('pappaya.subject', 'Subject')
    
    _sql_constraints = [
        ('unique_reigister',
         'unique(name,code)',
         'Register  must be unique per Attendance.'),
    ]
    
    
    @api.onchange('course_id')
    def onchange_course(self):
        self.batch_id = False
        
    @api.one
    @api.constrains('company_id','university_id')
    def _check_company_and_univ(self):
        if self.company_id and self.university_id:
            univ_search=self.env['pappaya.university'].search([('company_id','=',self.company_id.id),('id','=',self.university_id.id)])
            if not univ_search:
                raise ValidationError('Company and Institution Mismatch')
        
    @api.one
    def copy(self, default=None):
        raise ValidationError('You are not allowed to Duplicate')
        
