# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date
import dateutil.parser
from odoo.http import request


class ManpowerWRF(models.Model):
    _name = 'manpower.wrf'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    
    name = fields.Char('Name',size=128)
    academic_year_id = fields.Many2one('academic.year',string='Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    select_all = fields.Boolean(string='Select All')
    
    #from_deadline = fields.Date(string='From Date',default=_default_from_deadline)
    #to_deadline = fields.Date(string='Last Date',default=datetime.today().date().replace(month=3,day=30),readonly=True)
    line_ids = fields.One2many('department.wrf.line','manpower_wrf_id', string='Department List')
    state = fields.Selection([('draft','Draft'),('done','Done')],default='draft')
    
    april_first_deadline = fields.Date(string='From',default=datetime.today().date().replace(month=4,day=1),readonly=False)
    april_last_deadline = fields.Date(string='To',default=datetime.today().date().replace(month=4,day=30),readonly=False)
    
    #may_first_deadline = fields.Date(string='May First Deadline',default=datetime.today().date().replace(month=5,day=01),readonly=True)
    #may_last_deadline = fields.Date(string='May Last Deadline',default=datetime.today().date().replace(month=5,day=30),readonly=True)
    
#     @api.depends('to_deadline')            
#     def to_deadline(self):
#         for record in self:
#             current_date = datetime.today().date()
#             to_deadline = current_date.replace(month=3,day=30)
#             record.to_deadline = to_deadline
    
    @api.onchange('select_all')
    def onchange_select_all(self):
        for record in self:
            if record.select_all:
                for line in record.line_ids:
                    if not line.to_open:
                        line.to_open = True
    
    
    @api.onchange('name','academic_year_id','april_first_deadline','april_last_deadline')
    def onchange_set_department(self):
        for record in self:
            line_ids = None
            dept_list = []
            if record.name and record.academic_year_id and record.april_first_deadline and record.april_last_deadline:
                branch_sr = self.env['res.company'].search([('type','=','branch')])
                for branch in branch_sr:
                    all_dept_sr = self.env['hr.department'].search([('company_id','=',branch.id)])
                    for dept in all_dept_sr:
                        print (branch,branch.parent_id.parent_id.id,"34444444444444444")
                        dept_list.append({
                                            'organization_id':branch.parent_id.parent_id.id,
                                            'entities_id':branch.parent_id.id,
                                            'branch_id':branch.id,
                                            'state_id':branch.state_id.id,
                                            'office_type':branch.office_type_id.id,
                                            'programme_ids':[(6, 0,branch.programme_type_ids.ids)],
                                            'segment_ids':[(6, 0,branch.segment_type_ids.ids)],
                                            'manpower_wrf_id':record.id,
                                            'department_id':dept.id,
                                            'state':'draft'
                                            })
            record.line_ids =  dept_list       
                    
    
    @api.multi
    def to_open(self):
        for record in self:
            if datetime.strptime(record.april_first_deadline, "%Y-%m-%d").date() <= datetime.today().date() \
                and datetime.strptime(record.april_last_deadline, "%Y-%m-%d").date() >= datetime.today().date():
                
                for line in record.line_ids:
                    if line.to_open:
                        line.state = 'open'
                        line.onchange_department_id()
                        
                        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                        url = base_url + "/web#id=%s&view_type=form&model=department.wrf.line"%(line.id)
                        line.access_url = url
                        
                        template_obj = self.env['mail.template']
                        ir_model_data = self.env['ir.model.data']
                        template_id = ir_model_data.get_object_reference('pappaya_hr_recruitment', 'email_template_edi_dept_wise_open_recruitment')[1]
                        if template_id:
                            if line.department_id.manager_id.work_email:
                                template_obj.browse(template_id).send_mail(line.id, force_send=True)
                        
                line_state = record.line_ids.search([('id','in',record.line_ids.ids),('state','=','draft')])
                if record.line_ids and not line_state:
                    record.state='done'
            else:
                raise ValidationError(_("Manpower Workforce Requisition Form is not allowed to create after 30 April of every year"))    
        
class DepartmentWRFLine(models.Model):
    _name = 'department.wrf.line'
    _rec_name = 'department_id'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    
    to_open = fields.Boolean(string='Select')
    manpower_wrf_id = fields.Many2one('manpower.wrf',string='Manpower WRF')
    
    organization_id = fields.Many2one('res.company',string='Organization',domain=[('type','=','organization')])
    entities_id = fields.Many2one('res.company',string='Entities',domain=[('type','=','entity')])
    branch_id = fields.Many2one('res.company',string='Branch',domain=[('type','=','branch')])
    state_id = fields.Many2one('res.country.state',string='State',domain=[('country_id.is_active','=',True)])
    office_type = fields.Many2one('pappaya.office.type',string='Office Type')
    programme_ids = fields.Many2many('pappaya.programme','programme_department_wrl_rel','depart_wrf_id','programme_id',string='Programme')
    segment_ids = fields.Many2many('pappaya.segment','segment_department_wrl_rel','depart_wrf_id','segment_id',string='Segment')
    
    department_id = fields.Many2one('hr.department',string='Department')
    state = fields.Selection([('draft','Draft'),('open','Open'),('confirm','Confirm')],default='draft')
    line_ids = fields.One2many('designation.wrf.line','deparment_wrf_id', string='Designation List')
    
    april_first_deadline = fields.Date(string='April First Deadline',default=datetime.today().date().replace(month=4,day=1),readonly=False)
    april_last_deadline = fields.Date(string='April Last Deadline',default=datetime.today().date().replace(month=4,day=30),readonly=False)
    access_url = fields.Char('Access URL')
    
    @api.multi
    def to_confirm(self):
        for record in self:
            if datetime.strptime(record.april_first_deadline, "%Y-%m-%d").date() <= datetime.today().date() \
                and datetime.strptime(record.april_last_deadline, "%Y-%m-%d").date() >= datetime.today().date():
                for line in record.line_ids:
                    if line.new_count > 0:
                        self.env['requisition.form'].create({
                                                            'request_date':datetime.today().date(),
                                                            'location_id':record.branch_id.id,
                                                            'department_id':record.department_id.id,
                                                            'designation_id':line.designation_id.id,
                                                            'number_of_vacancies':line.new_count,
                                                            'salary_range':line.designation_id.budgeted_salary,
                                                            'year_of_experience':line.designation_id.year_of_experience,
                                                            })
            else:
                raise ValidationError(_("Manpower Workforce Requisition Form is not allowed to create after 30 April of every year"))
            record.state = 'confirm'
    
    @api.onchange('department_id','to_open')
    def onchange_department_id(self):
        for record in self:
            record.line_ids = None
            designation_list = []
            print (record.department_id.id,record.to_open,"2222222222222222222222")
            if record.department_id.id and record.to_open :
                
                designation_sr = self.env['hr.job'].search([('department_id','=',record.department_id.id)])
                print (designation_sr,"designation_srdesignation_srdesignation_sr")
                for designation in designation_sr:
                    designation_list.append({
                                            'deparment_wrf_id':record.id,
                                            'designation_id':designation.id,
                                            'exist_count':designation.no_of_employee,
                                            'already_no_of_recruitment':designation.no_of_recruitment,
                                            })
            record.line_ids = designation_list
                    
    
    
    

    

class DesignationWRFLine(models.Model):
    _name = 'designation.wrf.line'
    _rec_name = 'designation_id'
    
    deparment_wrf_id = fields.Many2one('department.wrf.line',string='Department WRF')    
    designation_id = fields.Many2one('hr.job',string='Designation')
    exist_count = fields.Integer(string='Exist Position')
    new_count = fields.Integer(string='New Position')
    already_no_of_recruitment = fields.Integer(string='Recruitment in progress')
    
    
    