# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Pappayabatch(models.Model):
    _inherit='pappaya.batch'
    
    batch_m2oneid = fields.Many2one('pappaya.incentive')


class Incentive(models.Model):
    _name = 'pappaya.incentive'
    _rec_name = 'academic_year_id'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    state_id = fields.Many2one('res.country.state', string='State', domain=[('country_id.is_active', '=', True)])
    district_id = fields.Many2one('state.district', string='District')
    student_type = fields.Selection([('day','Day'),('hostel','Hostel')], default='day', string='Student Type')
    appex_id = fields.Many2one('pappaya.course.provider')
    program_type = fields.Selection([('pre_admission','Pre Admission'),('admission','Admission')], string='Program Type')
    course_detail_ids = fields.One2many('pappaya.course', 'incentive_id')
    group_detail_ids = fields.One2many('pappaya.group','group_id')
    batch_detail_ids = fields.One2many('pappaya.batch','batch_m2oneid', string="test")
    batch_division_ids = fields.One2many('pappaya.batch.division','batch_division_id', string="division")
    emp_no = fields.Char(string="EMP No.")
    res_from_date = fields.Date(string="Res From Date")
    res_to_date = fields.Date(string="Res To Date")
#     order_by = fields.Selection([('designation','Designation'),('res_for_branch',"Res For Branch"),('res_no','Res No.'),('emp_no','Emp No.')])
    order_by = fields.Many2one('hr.job')
    type = fields.Selection([('school','School'),('pro','PRO'),('staff','Staff'),('college','College'),('agm','AGM / Principal')], string='Program Type')
    school = fields.Boolean('School')
    college = fields.Boolean('College')
    staff = fields.Boolean('Staff')
    pro = fields.Boolean('PRO')
    agm_principal = fields.Boolean('AGM/Principal')
    
    def onchange_apex_id(self):
        self.course_detail_ids = self.env['pappaya.course'].search([('course_provider_id','=',self.appex_id.id)]).ids
        self.group_detail_ids = self.env['pappaya.group'].search([('course_id','in',self.course_detail_ids.ids)]).ids
        self.batch_detail_ids = self.env['pappaya.batch'].search([('group_id','in',self.group_detail_ids.ids)]).ids
        self.batch_division_ids = self.env['pappaya.batch.division'].search([('batch_id','in',self.batch_detail_ids.ids)]).ids
    
    @api.multi
    @api.onchange('group_detail_ids')
    def onchange_group_detail_ids(self):
        self.course_detail_ids = self.group_detail_ids.mapped('course_id').ids
        self.batch_detail_ids = self.env['pappaya.batch'].search([('group_id','in',self.group_detail_ids.ids)]).ids
        
    @api.multi
    @api.onchange('batch_detail_ids')
    def onchange_batch_detail_ids(self):
        self.group_detail_ids = self.batch_detail_ids.mapped('group_id').ids
        self.batch_division_ids = self.env['pappaya.batch.division'].search([('batch_id','in',self.batch_detail_ids.ids)]).ids
        
    @api.multi
    @api.onchange('batch_division_ids')
    def onchange_batch_division_ids(self):
        self.batch_detail_ids = self.batch_division_ids.mapped('batch_id').ids


class PappayaCourse(models.Model):
    _inherit = 'pappaya.course'
    
    incentive_id = fields.Many2one('pappaya.incentive')
    
    
class PappayaGroup(models.Model):
    _inherit='pappaya.group'
    
    group_id = fields.Many2one('pappaya.incentive')


class PappayaBatchDivision(models.Model):
    _inherit='pappaya.batch.division'
    
    batch_division_id = fields.Many2one('pappaya.incentive')
    

    
    
            
            
        
