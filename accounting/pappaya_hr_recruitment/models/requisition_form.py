# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import dateutil.parser


class RequisitionForm(models.Model):
    _name = 'requisition.form'
    _rec_name = 'request_date'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'

    request_date = fields.Date('Request Date', default=lambda self:fields.Date.today())
    department_id = fields.Many2one('hr.department',string='Department')
    designation_id = fields.Many2one('hr.job', string='Position / Designation')
    number_of_vacancies = fields.Integer('No of Vacancies')
    organization_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    location_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    category_id = fields.Many2one('pappaya.employee.category',string='Category')
    subcategory_id = fields.Many2one('hr.employee.subcategory',string='Sub Category')
    subject_ids = fields.Many2many('pappaya.subject', string='Subjects')
    educational_qualification = fields.Many2many('hr.recruitment.degree','degree_requisition_form_rel','job_id','degree_id',string='Educational Qualifications')
    year_of_experience = fields.Integer(string='Years of experience')
    job_description = fields.Text(string='Job Description', size=100)
    salary_range = fields.Integer(string='Salary Range (Gross per month)',track_visibility='onchange')
    type_of_vacancy = fields.Selection([('replacement', 'Replacement'),('new', 'New')],default='new',string='Type of Vacancy')
    replace_employee_ids = fields.One2many('requisition.employee.list','requisition_form_id',string='Replace Employees')
    new_hiring_description = fields.Text(string='New Hiring Reason', size=200)
    
    expected_joining_time = fields.Date(string='Expected Joining Date')
    
    requested_by = fields.Many2one('res.users',string='Requested by',track_visibility='onchange')
    requested_employee_id = fields.Char(string='Employee ID',size=50)
    
    approved_by = fields.Many2one('res.users',string='Approved By',track_visibility='onchange')
    approved_designation = fields.Many2one('hr.job',string='Designation')
    remarks = fields.Text(string='Remarks If any',track_visibility='onchange',size=200)
    
    state = fields.Selection([('draft', 'Draft'),('request', 'Requested'),('Approve','Approved'),('cancel','Cancel')],default='draft',string='Status',track_visibility='onchange')

    entity_id = fields.Many2one('operating.unit', domain=[('type','=','entity')],string='Entity',related='location_id.parent_id')
    #legal_entity_id = fields.Many2one('pappaya.legal.entity','Legal Entity',related='location_id.legal_entity_id')
    state_id = fields.Many2one('res.country.state','State',related='location_id.state_id')
    office_type_id = fields.Many2one('pappaya.office.type',related='location_id.office_type_id',string="Office Type")
    is_budget_applicable = fields.Boolean(related="designation_id.is_budget_applicable")



    @api.onchange('location_id')
    def onchange_location_id(self):
        for record in self:
            record.category_id = record.subcategory_id = record.department_id = record.designation_id = None

    @api.constrains('designation_id', 'location_id', 'category_id', 'subcategory_id', 'department_id')
    def check_existing_record(self):
        for record in self:
            if record.designation_id:
                new_exsit_job_vancancy = 0.00
                exsit_job_vancancy = self.env['branch.wise.job.vecancy'].search([('branch_id','=',record.location_id.id),('job_id','=',record.designation_id.id)])
                new_exsit_job_vancancy = exsit_job_vancancy.new_count
                if new_exsit_job_vancancy > 0:
                    raise ValidationError(_("Already vacancy is open for this Designation"))
                
                if record.location_id and record.category_id and record.subcategory_id and record.department_id:
                    request = record.env['requisition.form'].search([('location_id','=',record.location_id.id),
                                                                     ('designation_id','=',record.designation_id.id),
                                                                     ('state','not in',['cancel','Approve'])
                                                                     ])
                    if len(request) > 1:
                        raise ValidationError(_("Already one Requisition form was created for this Designation"))
                    
                    job_description = record.env['pappaya.job.description'].search([('branch_id','=',record.location_id.id),
                                                                     ('job_id','=',record.designation_id.id),
                                                                     ('state','not in',['cancel','confirm'])
                                                                     ])
                    if len(job_description) > 1:
                        raise ValidationError(_("Already one Job Description was created for this Designation"))
                        
                        

    @api.onchange('location_id')
    def onchange_branch_id(self):
        for record in self:
            category = []
            record.category_id = None
            if record.location_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.location_id.office_type_id.id)])
                for job in job_positions:
                    category.append(job.category_id.id)
            return {'domain': {'category_id': [('id', 'in', category)]}} 
    
    @api.onchange('category_id')
    def onchange_branch_category_id(self):
        for record in self:
            subcategory = []
            record.subcategory_id = record.department_id = record.designation_id = None
            if record.location_id and record.category_id and record.location_id.office_type_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.location_id.office_type_id.id),('category_id', '=', record.category_id.id)])
                for job in job_positions:
                    subcategory.append(job.sub_category_id.id)
            return {'domain': {'subcategory_id': [('id', 'in', subcategory)]}} 
        
    
    @api.onchange('subcategory_id')
    def onchange_branch_subcategory_id(self):
        for record in self:
            department_ids = []
            record.department_id = None
            if record.category_id and record.office_type_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.office_type_id.id),
                                                           ('category_id', '=', record.category_id.id),
                                                           ('sub_category_id', '=', record.subcategory_id.id)
                                                           ])
                for job in job_positions:
                    department_ids.append(job.department_id.id)
            return {'domain': {'department_id': [('id', 'in', department_ids)]}}
        
        
    @api.onchange('department_id')
    def onchange_branch_designation_id(self):
        for record in self:
            record.designation_id = None
            job_id = []
            if record.location_id and record.category_id and record.subcategory_id and record.department_id:
                job_positions = self.env['hr.job'].search([('office_type_id', '=', record.location_id.office_type_id.id),
                                                           ('category_id', '=', record.category_id.id),
                                                           ('sub_category_id', '=', record.subcategory_id.id),
                                                           ('department_id', '=', record.department_id.id)
                                                           ])
                for job in job_positions:
                    job_id.append(job.id)
            return {'domain': {'designation_id': [('id', 'in', job_id)]}} 
    
            
    @api.constrains('number_of_vacancies','salary_range','year_of_experience','expected_joining_time','request_date','designation_id')
    def check_number_of_vacancies_salary(self):
        for record in self:
            
            exsit_job_vancancy = self.env['branch.wise.job.vecancy'].search([('branch_id','=',record.location_id.id),('job_id','=',record.designation_id.id)])
            if exsit_job_vancancy.new_count > 0:
                raise ValidationError(_("Already vacancy is open for this Designation"))
            
            if record.number_of_vacancies <= 0:
                raise ValidationError(_("No of Vacancies must be greater than Zero "))
            if record.salary_range <= 0.00:
                raise ValidationError(_("Salary Range (Gross per month) must be greater than Zero "))
            if record.year_of_experience < 0:
                raise ValidationError(_("Years of Experience must be greater than Zero"))

            if record.expected_joining_time:
                expected_joining = dateutil.parser.parse(record.expected_joining_time).date()
                if expected_joining and expected_joining <= datetime.today().date():
                    raise ValidationError(_("Expected Joining Date must be greater than Current Date"))

            request_date = dateutil.parser.parse(record.request_date).date()
            if request_date < datetime.today().date():
                raise ValidationError(_("Request Date must be greater than or equal to Current Date"))
    
    @api.multi
    def to_request(self):
        for record in self:
            if record.designation_id:
                if record.designation_id.no_of_recruitment > 0:
                    raise ValidationError(_("Already vacancy is open for this Designation"))
            if record.salary_range <= 0.00:
                raise ValidationError(_("Salary Range (Gross per month) must be greater than Zero "))
            if record.year_of_experience < 0:
                raise ValidationError(_("Years of Experience must be greater than Zero"))

            if record.expected_joining_time:
                expected_joining = dateutil.parser.parse(record.expected_joining_time).date()
                if expected_joining and expected_joining <= datetime.today().date():
                    raise ValidationError(_("Expected Joining Date must be greater than Current Date"))
            
            employee = self.env['hr.employee'].sudo().search([('user_id','=', self.env.uid)])
            record.requested_by = self.env.uid
            record.requested_employee_id = employee.emp_id
            record.state = 'request'
    
    @api.multi
    def to_approved(self):
        for record in self:
            if record.designation_id:
                if record.designation_id.no_of_recruitment > 0:
                    raise ValidationError(_("Already vacancy is open for this Designation"))
            self.env['pappaya.job.description'].sudo().create({
                                    'no_of_recruitment': record.number_of_vacancies,
                                    'educational_qualification_ids':[(6, 0,record.educational_qualification.ids)],
                                    'description':record.job_description,
                                    'year_of_experience':record.year_of_experience,
                                    'budgeted_salary':record.salary_range,
                                    'expected_date_of_joining':record.expected_joining_time,
                                    'approve_state':'draft',
                                    'initial_date':datetime.today().date(),
                                    'job_id':record.designation_id.id,
                                    'subject_ids':[(6, 0,record.subject_ids.ids)],
                                    'requisition_form_id':record.id,
                                    'branch_id':record.location_id.id,
                                    'name':record.designation_id.name,
                                    'department_id':record.department_id.id,
                                    })   
            employee = self.env['hr.employee'].sudo().search([('user_id','=', self.env.uid)])
            record.approved_by = self.env.uid
            record.approved_designation = employee.job_id.id
            record.state = 'Approve'
            
    @api.multi
    def to_cancel(self):
        for record in self:
            record.state = 'cancel'

    @api.one
    def copy(self, default=None):
        raise ValidationError('Sorry, You are not allowed to Duplicate')
    
class RequisitionEmployeeList(models.Model):
    _name = 'requisition.employee.list'
    
    requisition_form_id = fields.Many2one('requisition.form')
    emp_id = fields.Char(string='Employee ID',size=50)
    employee_id = fields.Many2one('hr.employee',string='Employee Name')

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for record in self:
            if record.employee_id:
                employee = self.env['hr.employee'].sudo().search([('id','=', record.employee_id.id),('active','=',False)])
                if employee:
                    record.emp_id = employee.emp_id
                else:
                    record.emp_id = False
                    #raise ValidationError("Please enter valid Employee ID")
            
        
        
        
        


