# -*- coding: utf-8 -*-

from openerp import models, fields,api,_
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError

class AttendanceLine(models.Model):
    _name = 'pappaya.attendance.line'
    _rec_name = 'attendance_id'
    
    @api.model
    def _default_company(self):
        user_id=self.env['res.users'].browse(self.env.uid)
        return user_id.company_id
        
    @api.model
    def default_university(self):
        university_ids=self.env['pappaya.university'].search([('user_ids','in',self.env.uid)])
        return university_ids and university_ids[0] 
    
    @api.model
    def default_department(self):
        department_ids=self.env['pappaya.department'].search([('user_ids','in',self.env.uid)])
        return department_ids and department_ids[0] 
    
    attendance_id = fields.Many2one(
        'pappaya.attendance.sheet', 'Attendance Sheet',)
        
    student_id = fields.Many2one('res.partner', 'Student',domain=[('user_type','=','student')], required=True)
    
    present_morning = fields.Boolean('FN Present ?', )
    
    present_afternoon =fields.Boolean('AN Present ?')
    
    company_id = fields.Many2one(
    'res.company', 'Organisation',select=True, default=_default_company )
    
    university_id = fields.Many2one(
    'res.company','Institution', default=default_university)
    
    # department_id=fields.Many2one(
    # 'pappaya.department','Department')
    
    course_id = fields.Many2one(
        'pappaya.grade', 'Grade',
        #~ related='attendance_id.register_id.course_id', store=True,
        readonly=True)
        
    batch_id = fields.Many2one(
        'pappaya.batch', 'Batch',
        #~ related='attendance_id.register_id.batch_id', store=True,
        readonly=True)
        
    remark = fields.Char('Remark',size=100)
    
    attendance_date = fields.Date(
        'Date', 
        #~ related='attendance_id.attendance_date', store=True,
        readonly=True)

    _sql_constraints = [
        ('unique_student',
         'unique(student_id,attendance_id,attendance_date)',
         'Student must be unique per Attendance.'),
    ]
    
    @api.one
    def copy(self, default=None):
        raise ValidationError('You are not allowed to Duplicate')
    
    # @api.one
    # @api.constrains('company_id','university_id')
    # def _check_company_and_univ(self):
    #     if self.company_id and self.university_id:
    #         univ_search=self.env['pappaya.university'].search([('company_id','=',self.company_id.id),('id','=',self.university_id.id)])
    #         if not univ_search:
    #             raise ValidationError('Company and Institution Mismatch')
    
    @api.onchange('attendance_id')
    def onchange_attendance_register(self):
        self.company_id = self.attendance_id.company_id.id
        self.university_id = self.attendance_id.university_id.id
        self.department_id = self.attendance_id.department_id.id
