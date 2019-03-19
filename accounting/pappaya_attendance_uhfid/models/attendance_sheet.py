# -*- coding: utf-8 -*-
from openerp import models, fields, api,_
from openerp.exceptions import UserError
from openerp.exceptions import ValidationError
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class AttendanceSheet(models.Model):
    _name = 'pappaya.attendance.sheet'
    
    
    @api.model
    def _default_company(self):
        user_id=self.env['res.users'].browse(self.env.uid)
        return user_id.company_id
        
    @api.model
    def default_university(self):
        university_ids=self.env['pappaya.university'].search([('user_ids','in',self.env.uid)])
        if not university_ids:
            univer_ids=self.env['res.users'].search([('id','=',self.env.uid)]).faculty_ids
            if univer_ids:
                return univer_ids[0].university_id
        return university_ids and university_ids[0]
    
    @api.model
    def default_department(self):
        department_ids=self.env['pappaya.department'].search([('user_ids','in',self.env.uid)])
        return department_ids and department_ids[0] 

    @api.one
    @api.depends('attendance_line.present_morning')
    def _total_present(self):
        self.total_present = len(self.attendance_line.filtered(
            lambda self: self.present_morning))

    @api.one
    @api.depends('attendance_line.present_morning')
    def _total_absent(self):
        self.total_absent = len(self.attendance_line.filtered(
            lambda self: self.present_morning is False))
    
    @api.one
    @api.depends('attendance_line.present_afternoon')
    def _total_present_fn(self):
        self.total_present_fn =len(self.attendance_line.filtered(
            lambda self: self.present_afternoon))
    
    @api.one
    @api.depends('attendance_line.present_afternoon')
    def _total_absent_fn(self):
        self.total_absent_fn =len(self.attendance_line.filtered(
            lambda self: self.present_afternoon is False))
    
    
    
    @api.multi
    @api.constrains('register_id')
    def _check_unique_register(self):
        if self.register_id:
            if len(self.env['pappaya.attendance.sheet'].search([('register_id','=',self.register_id.id),('attendance_date','=',self.attendance_date),('batch_id','=',self.batch_id.id)]).ids)>=1:
                raise ValidationError("Register already exists")
        
    name = fields.Char('Name', required=True, size=32)
    
    register_id = fields.Many2one(
        'pappaya.attendance.register', 'Register', required=True)
        
    company_id = fields.Many2one(
    'res.company', 'Organisation', default=_default_company )
    
    university_id = fields.Many2one(
    'pappaya.university','Institution', default=default_university)
    
    department_id=fields.Many2one(
    'pappaya.department','Department' )    
    
    course_id = fields.Many2one(
        'pappaya.course', related='register_id.course_id', store=True,
        readonly=True)
    batch_id = fields.Many2one(
        'pappaya.batch', 'Batch', related='register_id.batch_id', store=True,
        readonly=True)
    
    attendance_date = fields.Date(
        'Date', required=True, default=lambda self: fields.Date.today())
    attendance_line = fields.One2many(
        'pappaya.attendance.line', 'attendance_id', 'Attendance Line')
    total_present = fields.Integer(
        'Total Present FN', compute='_total_present')
    total_absent = fields.Integer(
        'Total Absent FN', compute='_total_absent')
    total_present_fn =fields.Integer(
            'Total Present AN' ,compute='_total_present_fn')
    total_absent_fn =fields.Integer(
            'Total Absent AN' ,compute='_total_absent_fn')
    
    faculty_id = fields.Many2one('pappaya.faculty', 'Faculty')
    
    _sql_constraints = [
     ('Unique_attendance_date_per_register', 'unique(register_id,attendance_date,batch_id)',
         "Register already exists with the date"),
    ]
    
    @api.one
    @api.constrains('company_id','university_id')
    def _check_company_and_univ(self):
        if self.company_id and self.university_id:
            univ_search=self.env['pappaya.university'].search([('company_id','=',self.company_id.id),('id','=',self.university_id.id)])
            if not univ_search:
                raise ValidationError('Company and Institution Mismatch')
    
    @api.one
    def copy(self, default=None):
        #~ default = dict(default or {})
        #~ default.update(
            #~ name=_("%s (copy)") % (self.name or ''), email='', user_id='')
        raise ValidationError('You are not allowed to Duplicate')
        
    
    
    @api.onchange('register_id')
    def onchange_attendance_register(self):
        self.company_id = self.register_id.company_id.id
        self.university_id = self.register_id.university_id.id
        self.department_id = self.register_id.department_id.id
    
    @api.multi
    @api.constrains('attendance_date') 
    def check_date(self):
        if datetime.strptime(self.attendance_date, DEFAULT_SERVER_DATE_FORMAT).date() > datetime.now().date():
            raise ValidationError('Future Attendance Entry Not Possible') 
        

    
    
    
    @api.multi
    def load_student(self):
        all_student_search = self.env['res.partner'].search(
                [('course_id', '=', self.register_id.course_id.id),
                 ('batch_id', '=', self.register_id.batch_id.id),('user_type','=','student')]
            )
        for i in all_student_search.ids:
            vals = {'student_id': i, 'present_morning': True,'present_afternoon':True ,'company_id':self.company_id.id,'university_id':self.university_id.id,
                        'department_id':self.department_id.id,
                        'attendance_id': self.id}
            self.env['pappaya.attendance.line'].create(vals)
    
   
