# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import re

location_type_selection = [('state_wise','State wise'),
                 ('cluster_wise','Cluster wise'),
                 ('district_wise', 'District wise'),
                 ('division_wise', 'Division wise'),
                 ('mandal_wise', 'Mandal wise'),
                 ('village_wise', 'Village wise'),
                 ('city_wise','City wise'),
                 ('ward_wise','Ward wise'),('area_wise','Area wise')]

class marketingStaffAllocation(models.Model):
    _name='marketing.staff.allocation'
    _description='Staff Allocation to Geo location or to Marketing Authourities'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))    
    name = fields.Char('Name',size=100)
    academic_type = fields.Selection([('academic','Academic'),('non_academic','Non Academic')], string='Academic Type', default='academic')
    staff_allocation_type = fields.Selection([('employee_wise','Employee Wise'),('location_wise','Location Wise')], string='Allocation Type', default='employee_wise')    
    # Employee wise Staff Allocation
    staff_hierarchy_id = fields.Many2one('staff.type.hierarchy', 'Staff Type Hierarchy')
    head_employee_id = fields.Many2one('hr.employee', 'Head')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')
    # Location wise Staff Allocation
    location_type = fields.Selection(selection=location_type_selection, string='Location Type')
    state_wise_staff_allocation_ids = fields.One2many('state.wise.staff.allocation', 'staff_allocation_id', 'State wise allocation')
    cluster_wise_staff_allocation_ids = fields.One2many('cluster.wise.staff.allocation', 'staff_allocation_id', 'Cluster wise allocation')
    district_wise_staff_allocation_ids = fields.One2many('district.wise.staff.allocation', 'staff_allocation_id', 'District wise allocation')
    division_wise_staff_allocation_ids = fields.One2many('division.wise.staff.allocation', 'staff_allocation_id', 'Division wise allocation')
    mandal_wise_staff_allocation_ids = fields.One2many('mandal.wise.staff.allocation', 'staff_allocation_id', 'Mandal wise allocation')
    village_wise_staff_allocation_ids = fields.One2many('village.wise.staff.allocation', 'staff_allocation_id', 'Village wise allocation')
    city_wise_staff_allocation_ids = fields.One2many('city.wise.staff.allocation', 'staff_allocation_id', 'City wise allocation')
    ward_wise_staff_allocation_ids = fields.One2many('ward.wise.staff.allocation', 'staff_allocation_id', 'Ward wise allocation')
    area_wise_staff_allocation_ids = fields.One2many('area.wise.staff.allocation', 'staff_allocation_id', 'Area wise allocation')
    
    _sql_constraints = [('academic_year_id_staff_hierarchy_id_head_employee_id_uniq', 
                        'unique(academic_year_id,staff_hierarchy_id,head_employee_id)', 
                        'Academic Year, Staff Type Hierarchy and Head Employee should be unique.')]
    
    @api.onchange('staff_allocation_type')
    def onchange_staff_allocation_type(self):
        if self.staff_allocation_type == 'employee_wise':
            self.location_type = False; self.area_wise_staff_allocation_ids = False
            self.state_wise_staff_allocation_ids = False; self.mandal_wise_staff_allocation_ids = False
            self.cluster_wise_staff_allocation_ids = False; self.village_wise_staff_allocation_ids = False
            self.district_wise_staff_allocation_ids = False; self.city_wise_staff_allocation_ids = False
            self.division_wise_staff_allocation_ids = False; self.ward_wise_staff_allocation_ids = False
        elif self.staff_allocation_type == 'location_wise':
            self.staff_hierarchy_id = False
            self.head_employee_id = False
            self.employee_ids = False
        
    @api.onchange('staff_hierarchy_id','head_employee_id','employee_ids')
    def onchange_staff_hierarchy_id(self):
        domain={}
        domain['head_employee_id'] = [('id','in',[])]; domain['employee_ids'] = [('id','in',[])]
        if self.staff_hierarchy_id:
            domain['head_employee_id'] = [('id','in',self.env['hr.employee'].search([('job_id','=',self.staff_hierarchy_id.job_id.id)]).ids)]
            job_ids = self.env['staff.type.hierarchy'].search([('parent_id','=',self.staff_hierarchy_id.id)]).mapped('job_id').ids
            if job_ids:
                domain['employee_ids'] = [('id','in',self.env['hr.employee'].search([('job_id','in',job_ids)]).ids)]
        return {'domain':domain}
    
class state_wise_staff_allocation(models.Model):
    _name='state.wise.staff.allocation'
    _description='State wise Staff Allocation'
    
    @api.multi
    def _compute_name(self):
        return 'Staff Allocation'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char(compute='_compute_name', string='Name')
    staff_allocation_id = fields.Many2one('marketing.staff.allocation', 'Staff Allocation')
    state_ids = fields.Many2many('res.country.state','States')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')
    
class cluster_wise_staff_allocation(models.Model):
    _name='cluster.wise.staff.allocation'
    _description='Cluster wise staff allocation'
    
    @api.multi
    def _compute_name(self):
        return 'Staff Allocation'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char(compute='_compute_name', string='Name')
    staff_allocation_id = fields.Many2one('marketing.staff.allocation', 'Staff Allocation')
    cluster_ids = fields.Many2many('pappaya.cluster','Clusters')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')
    
class district_wise_staff_allocation(models.Model):
    _name='district.wise.staff.allocation'
    _description='District wise Staff Allocation'
    
    @api.multi
    def _compute_name(self):
        return 'Staff Allocation'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char(compute='_compute_name', string='Name')
    staff_allocation_id = fields.Many2one('marketing.staff.allocation', 'Staff Allocation')
    district_ids = fields.Many2many('state.district','Districts')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')
    
class division_wise_staff_allocation(models.Model):
    _name='division.wise.staff.allocation'
    _description='Division wise staff allocation'
    
    @api.multi
    def _compute_name(self):
        return 'Staff Allocation'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char(compute='_compute_name', string='Name')
    staff_allocation_id = fields.Many2one('marketing.staff.allocation', 'Staff Allocation')
    division_ids = fields.Many2many('pappaya.division','Divisions')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')
    
class mandal_wise_staff_allocation(models.Model):
    _name='mandal.wise.staff.allocation'
    _description = 'Mandal wise Staff Allocation'
    
    @api.multi
    def _compute_name(self):
        return 'Staff Allocation'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char(compute='_compute_name', string='Name')
    staff_allocation_id = fields.Many2one('marketing.staff.allocation', 'Staff Allocation')
    mandal_ids = fields.Many2many('pappaya.mandal.marketing','Mandals')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')
    
class village_wise_staff_allocation(models.Model):
    _name='village.wise.staff.allocation'
    _description='Village wise Staff Allocation'
    
    @api.multi
    def _compute_name(self):
        return 'Staff Allocation'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char(compute='_compute_name', string='Name')
    staff_allocation_id = fields.Many2one('marketing.staff.allocation', 'Staff Allocation')
    village_ids = fields.Many2many('pappaya.village','Villages')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')
    
class city_wise_staff_allocation(models.Model):
    _name='city.wise.staff.allocation'
    _description='City wise Staff Allocation'
    
    @api.multi
    def _compute_name(self):
        return 'Staff Allocation'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char(compute='_compute_name', string='Name')
    staff_allocation_id = fields.Many2one('marketing.staff.allocation', 'Staff Allocation')
    city_ids = fields.Many2many('pappaya.city','Cities')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')
    
    
class ward_wise_staff_allocation(models.Model):
    _name='ward.wise.staff.allocation' 
    _description='Ward wise Staff Allocation' 
    
    @api.multi
    def _compute_name(self):
        return 'Staff Allocation'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char(compute='_compute_name', string='Name')
    staff_allocation_id = fields.Many2one('marketing.staff.allocation', 'Staff Allocation')
    ward_ids = fields.Many2many('pappaya.ward','Wards')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')
    
class area_wise_staff_allocation(models.Model):
    _name='area.wise.staff.allocation'
    _description='Area wise Staff Allocation'
    
    @api.multi
    def _compute_name(self):
        return 'Staff Allocation'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char(compute='_compute_name', string='Name')
    staff_allocation_id = fields.Many2one('marketing.staff.allocation', 'Staff Allocation')
    area_ids = fields.Many2many('pappaya.area','Areas')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees')  
    