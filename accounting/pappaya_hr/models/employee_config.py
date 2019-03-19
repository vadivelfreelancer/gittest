# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

class Job(models.Model):
    _inherit = "hr.job"
    _description='Designation'
    
    record_id                       = fields.Integer('ID')
    emp_no_ref                      = fields.Char('Created/Modified Employee No', size=9)
    code                            = fields.Char(string='Designation Code', size=5)
    job_master_id                   = fields.Many2one('hr.job.name', string='Designation')
    category_id                     = fields.Many2one('pappaya.employee.category', string='Category')
    sub_category_id                 = fields.Many2one('hr.employee.subcategory', string='Sub Category')
    office_type_id                  = fields.Many2one('pappaya.office.type', string="Office Type")
    is_budget_applicable            = fields.Boolean('Is Budget Applicable?')
    is_budget_applicable_from_job   = fields.Boolean('Is Budget Applicable?',related="sub_category_id.is_academic")
    entity_id                       = fields.Many2one('operating.unit', 'Entity',domain=[('type','=','entity')])

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
            job = self.env['hr.job.name'].search([('name', '=', vals.get('name'))])
            vals['job_master_id'] = job.id
        if vals.get('job_master_id'):
            job = self.env['hr.job.name'].search([('id', '=', vals.get('job_master_id'))])
            vals['name'] = job.name
        if vals.get('sub_category_id'):
            category_id = self.env['hr.employee.subcategory'].sudo().browse(vals.get('sub_category_id'))
            if category_id.is_academic:
                vals['is_budget_applicable'] = True
        return super(Job, self.with_context(mail_create_nosubscribe=True)).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
            job = self.env['hr.job.name'].search([('name', '=', vals.get('name'))])
            vals['job_master_id'] = job.id
        if vals.get('job_master_id'):
            job = self.env['hr.job.name'].search([('id', '=', vals.get('job_master_id'))])
            vals['name'] = job.name
        return super(Job, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name),('office_type_id', '=', self.office_type_id.id),('department_id', '=', self.department_id.id), \
                                   ('category_id', '=', self.category_id.id),('sub_category_id', '=', self.sub_category_id.id)])) > 1:
            raise ValidationError("Designation already exists")
        
    @api.constrains('record_id')
    def validate_of_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")
        

class Department(models.Model):
    _inherit = "hr.department"
    _description = 'Department'
    
    name = fields.Char('Name', required=False,size=100)
    # department_master_id = fields.Many2one('hr.department.name', string='Department')
    record_id = fields.Integer('ID')
    code = fields.Char(string='Department Code', size=5)
    # category_id = fields.Many2one('pappaya.employee.category', string='Category')
    # sub_category_id = fields.Many2one('hr.employee.subcategory', string='Sub Category')
    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    entity_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','entity')],index=True)
    # office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")

    # @api.onchange('department_master_id')
    # def get_department_master_name(self):
    #     for record in self:
    #         record.name = record.department_master_id.name


    @api.constrains('record_id')
    def validate_of_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
            # department = self.env['hr.department.name'].search([('name', '=', vals.get('name'))])
            # vals['department_master_id'] = department.id
        # if vals.get('department_master_id'):
        #     department = self.env['hr.department.name'].search([('id', '=', vals.get('department_master_id'))])
        #     vals['name'] = department.name
        department = super(Department, self.with_context(mail_create_nosubscribe=True)).create(vals)
        manager = self.env['hr.employee'].browse(vals.get("manager_id"))
        if manager.user_id:
            department.message_subscribe_users(user_ids=manager.user_id.ids)
        return department

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        #     department = self.env['hr.department.name'].search([('name', '=', vals.get('name'))])
        #     vals['department_master_id'] = department.id
        # if vals.get('department_master_id'):
        #     department = self.env['hr.department.name'].search([('id', '=', vals.get('department_master_id'))])
        #     vals['name'] = department.name
        if 'manager_id' in vals:
            manager_id = vals.get("manager_id")
            if manager_id:
                manager = self.env['hr.employee'].browse(manager_id)
                # subscribe the manager user
                if manager.user_id:
                    self.message_subscribe_users(user_ids=manager.user_id.ids)
            # set the employees's parent to the new manager
            self._update_employee_manager(manager_id)
        return super(Department, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.company_id = None
            self.entity_id = None
            # self.office_type_id = None
            # self.office_type_id = None
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name)])) > 1:
            raise ValidationError("Department already exists")
