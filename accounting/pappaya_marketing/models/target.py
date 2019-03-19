# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import re
from lxml import etree
from odoo.osv.orm import setup_modifiers

location_type_selection = [('state_wise','State wise'),
                 ('cluster_wise','Cluster wise'),
                 ('district_wise', 'District wise'),
                 ('division_wise', 'Division wise'),
                 ('mandal_wise', 'Mandal wise'),
                 ('village_wise', 'Village wise'),
                 ('city_wise','City wise'),
                 ('ward_wise','Ward wise'),('area_wise','Area wise'),('branch_wise','Branch wise')]

class ir_model_fields(models.Model):
    _inherit='ir.model.fields'
     
    @api.multi
    def name_get(self):
        res = []
        for field in self:
            if 'marketing_target' in self._context and self._context['marketing_target']:
                res.append((field.id, '%s' % (field.field_description)))
            else:
                res.append((field.id, '%s (%s)' % (field.field_description, field.model)))
        return res

""" Marketing Target Object Master"""

class marketing_target_object(models.Model):
    _name = 'marketing.target.object'
    _description = 'Marketing Target Object'
    _order = 'sequence asc'
    
    def _select_models(self):
        model_ids = self.env['ir.model'].sudo().search([])
        return ( [(r.model, r.name) for r in model_ids] or [('','')] )
    
    name = fields.Char('Name',size=100)
    model_id = fields.Many2one('ir.model', 'Master Object', required=True)
    sequence = fields.Integer(help="Used to order the target objects")
    description = fields.Text('Description',size=300)
    
    @api.onchange('model_id')
    def onchange_model_id(self):
        self.name = self.model_id.name
        
    @api.constrains('model_id')
    def _check_duplication(self):
        if self.sudo().search_count([('model_id','=',self.model_id.id)]) > 1:
            raise ValidationError("Given master object already exists.")
        
"""Marketing Target Master"""

class marketingTarget(models.Model):
    _name = 'marketing.target'
    _description = "Marketing Target"

    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char('Name',size=100)
    description = fields.Text('Description',size=300)
    target_line_ids = fields.One2many('marketing.target.line', 'target_id', 'Target Allocation', required=True)
    target_type = fields.Selection([('physical', 'Physical'),('logical', 'Logical')], string='Target Type', default="physical")
    state = fields.Selection([('draft','Draft'),('active','Active'),('archive','Archive')], string='State', default='draft')
    sequence = fields.Integer('Seaquence')
    
    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.name = self.env['res.company']._validate_name(self.name)

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(marketingTarget, self).write(vals)
    
    @api.constrains('academic_year_id','name','target_type','sequence')
    def validate(self):
        if self.academic_year_id and self.name and self.target_type:
            if self.sudo().search_count([('academic_year_id','=',self.academic_year_id.id),('name','=',self.name)]) > 1:
                raise ValidationError("Name already exists with given academic year.")
            if self.sudo().search_count([('academic_year_id','=',self.academic_year_id.id),('sequence','=',self.sequence)]) > 1:
                raise ValidationError("Sequence already exists with given academic year.")
        if not self.target_line_ids:
            raise ValidationError("Please fill Target Details.")
            
    
"""Master Target Lines"""
class marketingTargetLine(models.Model):
    _name='marketing.target.line'
    _description = 'Marketing Target Line'
    _rec_name = 'target_ref'
    
    @api.multi
    def _select_models(self):
        models = []
        for target_obj in self.env['marketing.target.object'].search([]):
            models.append((target_obj.model_id.model or '', target_obj.name or ''))
        return models
    
    target_id = fields.Many2one('marketing.target', 'Target ID')
    target_ref = fields.Reference(selection=_select_models, string="Target Object")
    admission_model_id = fields.Many2one('ir.model', 'Admisison Object')
    admission_field = fields.Many2one('ir.model.fields', string='Admission Field')
    logical_condition = fields.Selection([('and','AND'),('or','OR'),('not','NOT')], default='and')
    description = fields.Text('Description',size=300)
    
    @api.model
    def default_get(self, fields):
        res = super(marketingTargetLine, self).default_get(fields)
        if self.env['ir.model'].sudo().search([('name','=','pappaya.admission')]):
            res['admission_model_id'] = self.env['ir.model'].sudo().search([('name','=','pappaya.admission')]).id
        return res
    
    @api.constrains('target_id', 'target_ref')
    def _check_duplication(self):
        record_count = 0
        if self.target_id and self.target_ref:
            for rec in self.sudo().search([('target_id','=',self.target_id.id)]):
                if rec.target_ref.id == self.target_ref.id:
                    record_count +=1
            print (record_count, "record_count")
            if record_count > 1:
                raise ValidationError("Target Object cannot be duplicate.")
        return True
    
class target_allocation(models.Model):
    _name='target.allocation'
    _description = 'Target Allocation'
    
    @api.multi
    @api.onchange('target_allocation_line_ids')
    def _get_total_count(self):
        total = 0
        for record in self:
            for sub in record.target_allocation_line_ids:
                total += sub.target_sub_total
            record.total_target_count = total

    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)])) 
    name = fields.Char('Name',size=100)
    target_allocation_type = fields.Selection([('employee_wise','Employee Wise'),('location_wise','Location Wise')], string='Allocation Type', default='employee_wise')
    academic_type = fields.Selection([('academic','Academic'),('non_academic','Non Academic')],'Academic Type', default='non_academic')
    # Employee wise target Allocation
    staff_hierarchy_id = fields.Many2one('staff.type.hierarchy', 'Staff Hierarchy')
    head_employee_id = fields.Many2one('hr.employee', 'Head')
    # Location wise allocation
    location_type = fields.Selection(selection=location_type_selection, string='Location Type')
    # fields for add domain/filter
    state_ids = fields.Many2many(comodel_name='res.country.state', string='States')
    cluster_ids = fields.Many2many(comodel_name='pappaya.cluster', string='Clusters')
    district_ids = fields.Many2many(comodel_name='state.district', string='Districts')
    division_ids = fields.Many2many(comodel_name='pappaya.division', string='Divisions')
    mandal_ids = fields.Many2many(comodel_name='pappaya.mandal.marketing', string='Mandals')
    city_district_ids = fields.Many2many(comodel_name='state.district', string='Districts')
    city_ids = fields.Many2many(comodel_name='pappaya.city', string='Cities')
    ward_ids = fields.Many2many(comodel_name='pappaya.ward', string='Wards')
    
    state_target_allocation_line = fields.One2many('state.target.allocation.line', 'target_allocation_id', 'State Target Lines')
    cluster_target_allocation_line = fields.One2many('cluster.target.allocation.line', 'target_allocation_id', 'Cluster Target Lines')
    district_target_allocation_line = fields.One2many('district.target.allocation.line', 'target_allocation_id', 'District Target Lines')
    division_target_allocation_line = fields.One2many('division.target.allocation.line', 'target_allocation_id', 'Division Target Lines')
    mandal_target_allocation_line = fields.One2many('mandal.target.allocation.line', 'target_allocation_id', 'Mandal Target Lines')
    village_target_allocation_line = fields.One2many('village.target.allocation.line', 'target_allocation_id', 'Village Target Lines')
    city_target_allocation_line = fields.One2many('city.target.allocation.line', 'target_allocation_id', 'City Target Lines')
    ward_target_allocation_line = fields.One2many('ward.target.allocation.line', 'target_allocation_id', 'Ward Target Lines')
    area_target_allocation_line = fields.One2many('area.target.allocation.line', 'target_allocation_id', 'Area Target Lines')
    branch_target_allocation_line = fields.One2many('branch.target.allocation.line', 'target_allocation_id', 'Branch Target Lines')
    
    total_target_count = fields.Integer(compute='_get_total_count', string='Total Target')
    state = fields.Selection([('draft','Draft'),('active','Active'),('cancel','Cancel'),('archive','Archive')], string='State', default='draft')
    target_allocation_line_ids = fields.One2many('target.allocation.line', 'target_allocation_id', string='Target Allocation Lines')

    @api.onchange('target_allocation_type')
    def onchnage_target_allocation_type(self):
        if self.target_allocation_type == 'employee_wise':
            self.location_type = False
            self.state_target_allocation_line = self.cluster_target_allocation_line = self.division_target_allocation_line = \
            self.district_target_allocation_line = self.mandal_target_allocation_line = self.village_target_allocation_line = \
            self.city_target_allocation_line = self.ward_target_allocation_line = self.area_target_allocation_line = \
            self.branch_target_allocation_line = False
            self.state_ids = self.cluster_ids = self.district_ids = self.division_ids = self.mandal_ids = self.city_district_ids = \
            self.city_ids = self.ward_ids = False
        if self.target_allocation_type == 'location_wise':
            self.staff_hierarchy_id = False
            
    @api.onchange('academic_type')
    def onchange_academic_type(self):
        self.staff_hierarchy_id = False
    
    @api.onchange('staff_hierarchy_id')
    def onchange_staff_hierarchy_id(self):
        domain={}
        self.target_allocation_line_ids = False
        self.head_employee_id = False
        domain['head_employee_id'] = [('id','in',[])]
        if self.staff_hierarchy_id:
            job_id = self.staff_hierarchy_id.parent_id.job_id
            domain['head_employee_id'] = [('id','in',self.env['hr.employee'].search([('id','!=',1),('job_id','=',job_id.id)]).ids)]            
        return {'domain':domain}
    
    @api.onchange('head_employee_id')
    def onchange_head_employee_id(self):
        self.target_allocation_line_ids = False
        if not self.head_employee_id:
            self.target_allocation_line_ids.update({'head_employee_id':False})
        if self.head_employee_id:
            allocation_id = self.env['marketing.staff.allocation'].search([('academic_year_id','=',self.academic_year_id.id),('head_employee_id','=',self.head_employee_id.id)], limit=1)
            if allocation_id:
                target_allocation_line_ids = []
                for employee in allocation_id.employee_ids:
                    target_allocation_line_ids.append((0,0,{
                        'head_employee_id':self.head_employee_id.id,
                        'employee_id':employee.id,
                        'academic_year_id':self.academic_year_id.id
                        }))
                if target_allocation_line_ids:
                    self.target_allocation_line_ids = target_allocation_line_ids    

    """ Auto Popupulate for District based on cluster and state """
    @api.onchange('state_ids','cluster_ids')
    def onchange_state_ids(self):
        self.district_target_allocation_line = False
        # state_ids = self.state_ids.ids + self.state_target_allocation_line.mapped('state_id').ids
        # state_ids = self.state_ids.ids
        district_ids = self.env['state.district'].search([('state_id','in',self.state_ids.ids)]).ids
        # district_ids += self.cluster_ids.mapped('district_ids_m2m').ids+self.cluster_target_allocation_line.mapped('cluster_id').mapped('district_ids_m2m').ids
        district_ids += self.cluster_ids.mapped('district_ids_m2m').ids
        if district_ids:
            for district in self.env['state.district'].search([('id','in',list(set(district_ids)))]):
                if district.id not in self.district_target_allocation_line.mapped('district_id').ids:
                    self.district_target_allocation_line+=self.district_target_allocation_line.new({'district_id':district.id})
            
    """ Auto Popupulate for Mandal based on district and division """
    @api.onchange('district_ids','division_ids')
    def onchange_district_ids(self):
        self.mandal_target_allocation_line = False
        # district_ids = self.district_ids.ids+self.district_target_allocation_line.mapped('district_id').ids
        # district_ids = self.district_ids.ids
        mandal_ids = self.env['pappaya.mandal.marketing'].search([('district_id','in',self.district_ids.ids)]).ids
        # mandal_ids += self.division_ids.ids+self.division_target_allocation_line.mapped('division_id').mapped('mandal_ids_m2m').ids
        mandal_ids += self.division_ids.mapped('mandal_ids_m2m').ids
        if mandal_ids:
            for mandal in self.env['pappaya.mandal.marketing'].search([('id','in',list(set(mandal_ids)))]):
                if mandal.id not in self.mandal_target_allocation_line.mapped('mandal_id').ids:
                    self.mandal_target_allocation_line += self.mandal_target_allocation_line.new({'mandal_id':mandal.id})
                    
    @api.onchange('mandal_ids')
    def onchange_mandal_ids(self):
        self.village_target_allocation_line = False
        for village in self.env['pappaya.village'].search([('mandal_id','in',self.mandal_ids.ids)]):
            if village.id not in self.village_target_allocation_line.mapped('village_id').ids:
                self.village_target_allocation_line += self.village_target_allocation_line.new({'village_id':village.id})
    
    @api.onchange('city_district_ids')
    def onchange_city_district_ids(self):
        self.city_target_allocation_line = False
        for city in self.env['pappaya.city'].search([('district_id','in',self.city_district_ids.ids)]):
            if city.id not in self.city_target_allocation_line.mapped('city_id').ids:
                self.city_target_allocation_line+= self.city_target_allocation_line.new({'city_id':city.id})
    
    @api.onchange('city_ids')
    def onchange_city_ids(self):
        self.ward_target_allocation_line = False
        for ward in self.env['pappaya.ward'].search([('city_id','in',self.city_ids.ids)]):
            if ward.id not in self.ward_target_allocation_line.mapped('ward_id').ids:
                self.ward_target_allocation_line+= self.ward_target_allocation_line.new({'ward_id':ward.id})
                
    @api.onchange('ward_ids')
    def onchange_ward_ids(self):
        self.area_target_allocation_line = False
        for area in self.env['pappaya.area'].search([('ward_id','in',self.ward_ids.ids)]):
            if area.id not in self.area_target_allocation_line.mapped('area_id').ids:
                self.area_target_allocation_line+=self.area_target_allocation_line.new({'area_id':area.id})

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(target_allocation, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,submenu=submenu)
        doc_lists = ['target_allocation_line_ids','state_target_allocation_line','district_target_allocation_line','cluster_target_allocation_line',
                     'division_target_allocation_line','mandal_target_allocation_line','village_target_allocation_line','city_target_allocation_line',
                     'ward_target_allocation_line','area_target_allocation_line','branch_target_allocation_line']
        
        if view_type == 'form':
            for doc_list in doc_lists:
                target_list = ['target_count1', 'target_count2', 'target_count3', 'target_count4', 
                               'target_count5', 'target_count6', 'target_count7', 'target_count8',
                               'target_count9', 'target_count10', 'target_count11', 'target_count12', 
                               'target_count13', 'target_count14', 'target_count15', 'target_count16',
                               'target_count17', 'target_count18', 'target_count19', 'target_count20',
                               'target_count21', 'target_count22', 'target_count23', 'target_count24',
                               'target_count25', 'target_count26', 'target_count27', 'target_count28',
                               'target_count29', 'target_count30']                
                
                doc = etree.XML(res['fields'][doc_list]['views']['tree']['arch'])
                print (self.academic_year_id.id, "$$$")
                for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',self.env.user.company_id.active_academic_year_id.id)], order='sequence'):
                    for target_field in target_list:
                        node = doc.xpath("//field[@name='"+target_field+"']")[0]
                        node.set('string', _(str(target_obj.name)))
                        target_list.remove(target_field)
                        break
                for target_field in target_list:
                    nodes = doc.xpath("//field[@name='" + target_field + "']")
                    for node in nodes:
                        node.set('invisible', 'True')
                        doc.remove(node)
                        setup_modifiers(node, res['fields'][doc_list]['views']['tree']['fields'][target_field])
                res['fields'][doc_list]['views']['tree']['arch'] = etree.tostring(doc)
        return res
            
    @api.multi
    def action_confirm(self):
        for record in self:
            if not record.target_allocation_line_ids:
                raise ValidationError("Target Allocation Details should not be empty.")
#             for line in record.target_allocation_line_ids:
#                 if not line.target_count > 0:
#                     raise ValidationError("Target count should be greater than 0.")
            record.state = 'active'
                     
    @api.multi
    def action_cancel(self):
        for record in self:
            record.state = 'cancel'
    
    @api.multi
    def action_archive(self):
        for record in self:
            record.state = 'archive'
    
    @api.multi
    def action_reset(self):
        for record in self:
            record.state = 'draft'       
        
class target_allocation_line(models.Model):
    _name='target.allocation.line'
    _description='Target Allocation Line'
    
    @api.multi
    @api.onchange('target_count1','target_count2','target_count3','target_count4','target_count5','target_count6','target_count7','target_count8',
                  'target_count9','target_count10','target_count11','target_count12','target_count13','target_count14','target_count15', 'target_count16',
                  'target_count17','target_count18','target_count19','target_count20','target_count21','target_count22','target_count23','target_count24',
                  'target_count25','target_count26','target_count27','target_count28','target_count29','target_count30')
    def _get_target_allocation_sub_total(self):
        for record in self:
            total = 0
            target_info = {}
            for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',record.academic_year_id.id)], order='sequence'):
                target_info.update({target_obj.id:record[(str('target_count')+str(target_obj.sequence+1))]})
                if target_obj.target_type == 'physical':
                    total += record[(str('target_count')+str(target_obj.sequence+1))]
            record.target_info = str(target_info)
            record.target_sub_total = total
        
    @api.multi
    def _select_models(self):
        models = []
        for target_obj in self.env['marketing.target.object'].search([]):
            models.append((target_obj.model_id.model or '', target_obj.name or ''))
        return models
    
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        domain = {}; domain['employee_id'] = [('id','in',[])]
        if self.target_allocation_id.head_employee_id:
            staff_allocation_id = self.env['marketing.staff.allocation'].search([('academic_year_id','=',self.academic_year_id.id),
                                                                                 ('head_employee_id','=',self.target_allocation_id.head_employee_id.id)], limit=1)
            if staff_allocation_id:
                domain['employee_id'] = [('id','in',staff_allocation_id.employee_ids.ids)]
        elif self.target_allocation_id.staff_hierarchy_id and not self.target_allocation_id.head_employee_id:
            job_id = self.target_allocation_id.staff_hierarchy_id.job_id.id
            domain['employee_id'] = [('id','in',self.env['hr.employee'].search([('id','!=',1),('job_id','=',job_id)]).ids)]
        return {'domain':domain}
    
    head_employee_id = fields.Many2one('hr.employee','Parent Head Employee')
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    target_allocation_id = fields.Many2one('target.allocation','Target Allocation ID')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    target_ref = fields.Reference(selection=_select_models, string="Target Object")

    # Fields For Dynamic target column    
    target_count1 = fields.Integer(string='Target Count 1')
    target_count2 = fields.Integer(string='Target Count 2')
    target_count3 = fields.Integer(string='Target Count 3')
    target_count4 = fields.Integer(string='Target Count 4')
    target_count5 = fields.Integer(string='Target Count 5')
    target_count6 = fields.Integer(string='Target Count 6')
    target_count7 = fields.Integer(string='Target Count 7')
    target_count8 = fields.Integer(string='Target Count 8')
    target_count9 = fields.Integer(string='Target Count 9')
    target_count10 = fields.Integer(string='Target Count 10')
    target_count11 = fields.Integer(string='Target Count 11')
    target_count12 = fields.Integer(string='Target Count 12')
    target_count13 = fields.Integer(string='Target Count 13')
    target_count14 = fields.Integer(string='Target Count 14')
    target_count15 = fields.Integer(string='Target Count 15')
    target_count16 = fields.Integer(string='Target Count 16')
    target_count17 = fields.Integer(string='Target Count 17')
    target_count18 = fields.Integer(string='Target Count 18')
    target_count19 = fields.Integer(string='Target Count 19')
    target_count20 = fields.Integer(string='Target Count 20')
    target_count21 = fields.Integer(string='Target Count 21')
    target_count22 = fields.Integer(string='Target Count 22')
    target_count23 = fields.Integer(string='Target Count 23')
    target_count24 = fields.Integer(string='Target Count 24')
    target_count25 = fields.Integer(string='Target Count 25')
    target_count26 = fields.Integer(string='Target Count 26')
    target_count27 = fields.Integer(string='Target Count 27')
    target_count28 = fields.Integer(string='Target Count 28')
    target_count29 = fields.Integer(string='Target Count 29')
    target_count30 = fields.Integer(string='Target Count 30')

    target_info = fields.Text('Target Information',size=300)
    target_sub_total = fields.Integer(compute='_get_target_allocation_sub_total', string='Total')
    
    @api.model
    def default_get(self, fields):
        res = super(target_allocation_line, self).default_get(fields)
        res['head_employee_id'] = self._context.get('head_employee_id') or False
        return res
    
class state_target_allocation_line(models.Model):
    _name='state.target.allocation.line'
    _description='State Target Allocation Line'
    
    @api.multi
    @api.onchange('target_count1','target_count2','target_count3','target_count4','target_count5','target_count6','target_count7','target_count8',
                  'target_count9','target_count10','target_count11','target_count12','target_count13','target_count14','target_count15', 'target_count16',
                  'target_count17','target_count18','target_count19','target_count20','target_count21','target_count22','target_count23','target_count24',
                  'target_count25','target_count26','target_count27','target_count28','target_count29','target_count30')
    def _get_target_allocation_sub_total(self):
        for record in self:
            total = 0
            target_info = {}
            for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',record.academic_year_id.id)], order='sequence'):
                target_info.update({target_obj.id:record[(str('target_count')+str(target_obj.sequence+1))]})
                if target_obj.target_type == 'physical':
                    total += record[(str('target_count')+str(target_obj.sequence+1))]
            record.target_info = str(target_info)
            record.target_sub_total = total
    
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    target_allocation_id = fields.Many2one('target.allocation','Target Allocation ID')

    state_id = fields.Many2one('res.country.state', 'State', required=True)
    # Fields For Dynamic target column    
    target_count1 = fields.Integer(string='Target Count 1')
    target_count2 = fields.Integer(string='Target Count 2')
    target_count3 = fields.Integer(string='Target Count 3')
    target_count4 = fields.Integer(string='Target Count 4')
    target_count5 = fields.Integer(string='Target Count 5')
    target_count6 = fields.Integer(string='Target Count 6')
    target_count7 = fields.Integer(string='Target Count 7')
    target_count8 = fields.Integer(string='Target Count 8')
    target_count9 = fields.Integer(string='Target Count 9')
    target_count10 = fields.Integer(string='Target Count 10')
    target_count11 = fields.Integer(string='Target Count 11')
    target_count12 = fields.Integer(string='Target Count 12')
    target_count13 = fields.Integer(string='Target Count 13')
    target_count14 = fields.Integer(string='Target Count 14')
    target_count15 = fields.Integer(string='Target Count 15')
    target_count16 = fields.Integer(string='Target Count 16')
    target_count17 = fields.Integer(string='Target Count 17')
    target_count18 = fields.Integer(string='Target Count 18')
    target_count19 = fields.Integer(string='Target Count 19')
    target_count20 = fields.Integer(string='Target Count 20')
    target_count21 = fields.Integer(string='Target Count 21')
    target_count22 = fields.Integer(string='Target Count 22')
    target_count23 = fields.Integer(string='Target Count 23')
    target_count24 = fields.Integer(string='Target Count 24')
    target_count25 = fields.Integer(string='Target Count 25')
    target_count26 = fields.Integer(string='Target Count 26')
    target_count27 = fields.Integer(string='Target Count 27')
    target_count28 = fields.Integer(string='Target Count 28')
    target_count29 = fields.Integer(string='Target Count 29')
    target_count30 = fields.Integer(string='Target Count 30')

    target_info = fields.Text('Target Information',size=300)
    target_sub_total = fields.Integer(compute='_get_target_allocation_sub_total', string='Total')
    
class cluster_target_allocation_line(models.Model):
    _name='cluster.target.allocation.line'
    _description='State Target Allocation Line'
    
    @api.multi
    @api.onchange('target_count1','target_count2','target_count3','target_count4','target_count5','target_count6','target_count7','target_count8',
                  'target_count9','target_count10','target_count11','target_count12','target_count13','target_count14','target_count15', 'target_count16',
                  'target_count17','target_count18','target_count19','target_count20','target_count21','target_count22','target_count23','target_count24',
                  'target_count25','target_count26','target_count27','target_count28','target_count29','target_count30')
    def _get_target_allocation_sub_total(self):
        for record in self:
            total = 0
            target_info = {}
            for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',record.academic_year_id.id)], order='sequence'):
                target_info.update({target_obj.id:record[(str('target_count')+str(target_obj.sequence+1))]})
                if target_obj.target_type == 'physical':
                    total += record[(str('target_count')+str(target_obj.sequence+1))]
            record.target_info = str(target_info)
            record.target_sub_total = total
    
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    target_allocation_id = fields.Many2one('target.allocation','Target Allocation ID')
    
    cluster_id = fields.Many2one('pappaya.cluster', 'Cluster', required=True)
    # Fields For Dynamic target column    
    target_count1 = fields.Integer(string='Target Count 1')
    target_count2 = fields.Integer(string='Target Count 2')
    target_count3 = fields.Integer(string='Target Count 3')
    target_count4 = fields.Integer(string='Target Count 4')
    target_count5 = fields.Integer(string='Target Count 5')
    target_count6 = fields.Integer(string='Target Count 6')
    target_count7 = fields.Integer(string='Target Count 7')
    target_count8 = fields.Integer(string='Target Count 8')
    target_count9 = fields.Integer(string='Target Count 9')
    target_count10 = fields.Integer(string='Target Count 10')
    target_count11 = fields.Integer(string='Target Count 11')
    target_count12 = fields.Integer(string='Target Count 12')
    target_count13 = fields.Integer(string='Target Count 13')
    target_count14 = fields.Integer(string='Target Count 14')
    target_count15 = fields.Integer(string='Target Count 15')
    target_count16 = fields.Integer(string='Target Count 16')
    target_count17 = fields.Integer(string='Target Count 17')
    target_count18 = fields.Integer(string='Target Count 18')
    target_count19 = fields.Integer(string='Target Count 19')
    target_count20 = fields.Integer(string='Target Count 20')
    target_count21 = fields.Integer(string='Target Count 21')
    target_count22 = fields.Integer(string='Target Count 22')
    target_count23 = fields.Integer(string='Target Count 23')
    target_count24 = fields.Integer(string='Target Count 24')
    target_count25 = fields.Integer(string='Target Count 25')
    target_count26 = fields.Integer(string='Target Count 26')
    target_count27 = fields.Integer(string='Target Count 27')
    target_count28 = fields.Integer(string='Target Count 28')
    target_count29 = fields.Integer(string='Target Count 29')
    target_count30 = fields.Integer(string='Target Count 30')

    target_info = fields.Text('Target Information',size=300)
    target_sub_total = fields.Integer(compute='_get_target_allocation_sub_total', string='Total')
        
class district_target_allocation_line(models.Model):
    _name='district.target.allocation.line'
    _description='State Target Allocation Line'
    
    @api.multi
    @api.onchange('target_count1','target_count2','target_count3','target_count4','target_count5','target_count6','target_count7','target_count8',
                  'target_count9','target_count10','target_count11','target_count12','target_count13','target_count14','target_count15', 'target_count16',
                  'target_count17','target_count18','target_count19','target_count20','target_count21','target_count22','target_count23','target_count24',
                  'target_count25','target_count26','target_count27','target_count28','target_count29','target_count30')
    def _get_target_allocation_sub_total(self):
        for record in self:
            total = 0
            target_info = {}
            for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',record.academic_year_id.id)], order='sequence'):
                target_info.update({target_obj.id:record[(str('target_count')+str(target_obj.sequence+1))]})
                if target_obj.target_type == 'physical':
                    total += record[(str('target_count')+str(target_obj.sequence+1))]
            record.target_info = str(target_info)
            record.target_sub_total = total
    
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    target_allocation_id = fields.Many2one('target.allocation','Target Allocation ID')

    district_id = fields.Many2one('state.district', 'District', required=True)
    # Fields For Dynamic target column    
    target_count1 = fields.Integer(string='Target Count 1')
    target_count2 = fields.Integer(string='Target Count 2')
    target_count3 = fields.Integer(string='Target Count 3')
    target_count4 = fields.Integer(string='Target Count 4')
    target_count5 = fields.Integer(string='Target Count 5')
    target_count6 = fields.Integer(string='Target Count 6')
    target_count7 = fields.Integer(string='Target Count 7')
    target_count8 = fields.Integer(string='Target Count 8')
    target_count9 = fields.Integer(string='Target Count 9')
    target_count10 = fields.Integer(string='Target Count 10')
    target_count11 = fields.Integer(string='Target Count 11')
    target_count12 = fields.Integer(string='Target Count 12')
    target_count13 = fields.Integer(string='Target Count 13')
    target_count14 = fields.Integer(string='Target Count 14')
    target_count15 = fields.Integer(string='Target Count 15')
    target_count16 = fields.Integer(string='Target Count 16')
    target_count17 = fields.Integer(string='Target Count 17')
    target_count18 = fields.Integer(string='Target Count 18')
    target_count19 = fields.Integer(string='Target Count 19')
    target_count20 = fields.Integer(string='Target Count 20')
    target_count21 = fields.Integer(string='Target Count 21')
    target_count22 = fields.Integer(string='Target Count 22')
    target_count23 = fields.Integer(string='Target Count 23')
    target_count24 = fields.Integer(string='Target Count 24')
    target_count25 = fields.Integer(string='Target Count 25')
    target_count26 = fields.Integer(string='Target Count 26')
    target_count27 = fields.Integer(string='Target Count 27')
    target_count28 = fields.Integer(string='Target Count 28')
    target_count29 = fields.Integer(string='Target Count 29')
    target_count30 = fields.Integer(string='Target Count 30')

    target_info = fields.Text('Target Information',size=300)
    target_sub_total = fields.Integer(compute='_get_target_allocation_sub_total', string='Total')
    
    
class division_target_allocation_line(models.Model):
    _name='division.target.allocation.line'
    _description='State Target Allocation Line'
    
    @api.multi
    @api.onchange('target_count1','target_count2','target_count3','target_count4','target_count5','target_count6','target_count7','target_count8',
                  'target_count9','target_count10','target_count11','target_count12','target_count13','target_count14','target_count15', 'target_count16',
                  'target_count17','target_count18','target_count19','target_count20','target_count21','target_count22','target_count23','target_count24',
                  'target_count25','target_count26','target_count27','target_count28','target_count29','target_count30')
    def _get_target_allocation_sub_total(self):
        for record in self:
            total = 0
            target_info = {}
            for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',record.academic_year_id.id)], order='sequence'):
                target_info.update({target_obj.id:record[(str('target_count')+str(target_obj.sequence+1))]})
                if target_obj.target_type == 'physical':
                    total += record[(str('target_count')+str(target_obj.sequence+1))]
            record.target_info = str(target_info)
            record.target_sub_total = total
    
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    target_allocation_id = fields.Many2one('target.allocation','Target Allocation ID')

    division_id = fields.Many2one('pappaya.division', 'Division', required=True)
    # Fields For Dynamic target column    
    target_count1 = fields.Integer(string='Target Count 1')
    target_count2 = fields.Integer(string='Target Count 2')
    target_count3 = fields.Integer(string='Target Count 3')
    target_count4 = fields.Integer(string='Target Count 4')
    target_count5 = fields.Integer(string='Target Count 5')
    target_count6 = fields.Integer(string='Target Count 6')
    target_count7 = fields.Integer(string='Target Count 7')
    target_count8 = fields.Integer(string='Target Count 8')
    target_count9 = fields.Integer(string='Target Count 9')
    target_count10 = fields.Integer(string='Target Count 10')
    target_count11 = fields.Integer(string='Target Count 11')
    target_count12 = fields.Integer(string='Target Count 12')
    target_count13 = fields.Integer(string='Target Count 13')
    target_count14 = fields.Integer(string='Target Count 14')
    target_count15 = fields.Integer(string='Target Count 15')
    target_count16 = fields.Integer(string='Target Count 16')
    target_count17 = fields.Integer(string='Target Count 17')
    target_count18 = fields.Integer(string='Target Count 18')
    target_count19 = fields.Integer(string='Target Count 19')
    target_count20 = fields.Integer(string='Target Count 20')
    target_count21 = fields.Integer(string='Target Count 21')
    target_count22 = fields.Integer(string='Target Count 22')
    target_count23 = fields.Integer(string='Target Count 23')
    target_count24 = fields.Integer(string='Target Count 24')
    target_count25 = fields.Integer(string='Target Count 25')
    target_count26 = fields.Integer(string='Target Count 26')
    target_count27 = fields.Integer(string='Target Count 27')
    target_count28 = fields.Integer(string='Target Count 28')
    target_count29 = fields.Integer(string='Target Count 29')
    target_count30 = fields.Integer(string='Target Count 30')

    target_info = fields.Text('Target Information',size=300)
    target_sub_total = fields.Integer(compute='_get_target_allocation_sub_total', string='Total')
        
class mandal_target_allocation_line(models.Model):
    _name='mandal.target.allocation.line'
    _description='State Target Allocation Line'
    
    @api.multi
    @api.onchange('target_count1','target_count2','target_count3','target_count4','target_count5','target_count6','target_count7','target_count8',
                  'target_count9','target_count10','target_count11','target_count12','target_count13','target_count14','target_count15', 'target_count16',
                  'target_count17','target_count18','target_count19','target_count20','target_count21','target_count22','target_count23','target_count24',
                  'target_count25','target_count26','target_count27','target_count28','target_count29','target_count30')
    def _get_target_allocation_sub_total(self):
        for record in self:
            total = 0
            target_info = {}
            for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',record.academic_year_id.id)], order='sequence'):
                target_info.update({target_obj.id:record[(str('target_count')+str(target_obj.sequence+1))]})
                if target_obj.target_type == 'physical':
                    total += record[(str('target_count')+str(target_obj.sequence+1))]
            record.target_info = str(target_info)
            record.target_sub_total = total
    
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    target_allocation_id = fields.Many2one('target.allocation','Target Allocation ID')

    mandal_id = fields.Many2one('pappaya.mandal.marketing', 'State', required=True)
    # Fields For Dynamic target column    
    target_count1 = fields.Integer(string='Target Count 1')
    target_count2 = fields.Integer(string='Target Count 2')
    target_count3 = fields.Integer(string='Target Count 3')
    target_count4 = fields.Integer(string='Target Count 4')
    target_count5 = fields.Integer(string='Target Count 5')
    target_count6 = fields.Integer(string='Target Count 6')
    target_count7 = fields.Integer(string='Target Count 7')
    target_count8 = fields.Integer(string='Target Count 8')
    target_count9 = fields.Integer(string='Target Count 9')
    target_count10 = fields.Integer(string='Target Count 10')
    target_count11 = fields.Integer(string='Target Count 11')
    target_count12 = fields.Integer(string='Target Count 12')
    target_count13 = fields.Integer(string='Target Count 13')
    target_count14 = fields.Integer(string='Target Count 14')
    target_count15 = fields.Integer(string='Target Count 15')
    target_count16 = fields.Integer(string='Target Count 16')
    target_count17 = fields.Integer(string='Target Count 17')
    target_count18 = fields.Integer(string='Target Count 18')
    target_count19 = fields.Integer(string='Target Count 19')
    target_count20 = fields.Integer(string='Target Count 20')
    target_count21 = fields.Integer(string='Target Count 21')
    target_count22 = fields.Integer(string='Target Count 22')
    target_count23 = fields.Integer(string='Target Count 23')
    target_count24 = fields.Integer(string='Target Count 24')
    target_count25 = fields.Integer(string='Target Count 25')
    target_count26 = fields.Integer(string='Target Count 26')
    target_count27 = fields.Integer(string='Target Count 27')
    target_count28 = fields.Integer(string='Target Count 28')
    target_count29 = fields.Integer(string='Target Count 29')
    target_count30 = fields.Integer(string='Target Count 30')

    target_info = fields.Text('Target Information',size=300)
    target_sub_total = fields.Integer(compute='_get_target_allocation_sub_total', string='Total')
        
class village_target_allocation_line(models.Model):
    _name='village.target.allocation.line'
    _description='State Target Allocation Line'
    
    @api.multi
    @api.onchange('target_count1','target_count2','target_count3','target_count4','target_count5','target_count6','target_count7','target_count8',
                  'target_count9','target_count10','target_count11','target_count12','target_count13','target_count14','target_count15', 'target_count16',
                  'target_count17','target_count18','target_count19','target_count20','target_count21','target_count22','target_count23','target_count24',
                  'target_count25','target_count26','target_count27','target_count28','target_count29','target_count30')
    def _get_target_allocation_sub_total(self):
        for record in self:
            total = 0
            target_info = {}
            for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',record.academic_year_id.id)], order='sequence'):
                target_info.update({target_obj.id:record[(str('target_count')+str(target_obj.sequence+1))]})
                if target_obj.target_type == 'physical':
                    total += record[(str('target_count')+str(target_obj.sequence+1))]
            record.target_info = str(target_info)
            record.target_sub_total = total
    
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    target_allocation_id = fields.Many2one('target.allocation','Target Allocation ID')

    village_id = fields.Many2one('pappaya.village', 'Village', required=True)
    # Fields For Dynamic target column    
    target_count1 = fields.Integer(string='Target Count 1')
    target_count2 = fields.Integer(string='Target Count 2')
    target_count3 = fields.Integer(string='Target Count 3')
    target_count4 = fields.Integer(string='Target Count 4')
    target_count5 = fields.Integer(string='Target Count 5')
    target_count6 = fields.Integer(string='Target Count 6')
    target_count7 = fields.Integer(string='Target Count 7')
    target_count8 = fields.Integer(string='Target Count 8')
    target_count9 = fields.Integer(string='Target Count 9')
    target_count10 = fields.Integer(string='Target Count 10')
    target_count11 = fields.Integer(string='Target Count 11')
    target_count12 = fields.Integer(string='Target Count 12')
    target_count13 = fields.Integer(string='Target Count 13')
    target_count14 = fields.Integer(string='Target Count 14')
    target_count15 = fields.Integer(string='Target Count 15')
    target_count16 = fields.Integer(string='Target Count 16')
    target_count17 = fields.Integer(string='Target Count 17')
    target_count18 = fields.Integer(string='Target Count 18')
    target_count19 = fields.Integer(string='Target Count 19')
    target_count20 = fields.Integer(string='Target Count 20')
    target_count21 = fields.Integer(string='Target Count 21')
    target_count22 = fields.Integer(string='Target Count 22')
    target_count23 = fields.Integer(string='Target Count 23')
    target_count24 = fields.Integer(string='Target Count 24')
    target_count25 = fields.Integer(string='Target Count 25')
    target_count26 = fields.Integer(string='Target Count 26')
    target_count27 = fields.Integer(string='Target Count 27')
    target_count28 = fields.Integer(string='Target Count 28')
    target_count29 = fields.Integer(string='Target Count 29')
    target_count30 = fields.Integer(string='Target Count 30')

    target_info = fields.Text('Target Information',size=300)
    target_sub_total = fields.Integer(compute='_get_target_allocation_sub_total', string='Total')
        
class city_target_allocation_line(models.Model):
    _name='city.target.allocation.line'
    _description='State Target Allocation Line'
    
    @api.multi
    @api.onchange('target_count1','target_count2','target_count3','target_count4','target_count5','target_count6','target_count7','target_count8',
                  'target_count9','target_count10','target_count11','target_count12','target_count13','target_count14','target_count15', 'target_count16',
                  'target_count17','target_count18','target_count19','target_count20','target_count21','target_count22','target_count23','target_count24',
                  'target_count25','target_count26','target_count27','target_count28','target_count29','target_count30')
    def _get_target_allocation_sub_total(self):
        for record in self:
            total = 0
            target_info = {}
            for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',record.academic_year_id.id)], order='sequence'):
                target_info.update({target_obj.id:record[(str('target_count')+str(target_obj.sequence+1))]})
                if target_obj.target_type == 'physical':
                    total += record[(str('target_count')+str(target_obj.sequence+1))]
            record.target_info = str(target_info)
            record.target_sub_total = total
    
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    target_allocation_id = fields.Many2one('target.allocation','Target Allocation ID')

    city_id = fields.Many2one('pappaya.city', 'City', required=True)
    # Fields For Dynamic target column    
    target_count1 = fields.Integer(string='Target Count 1')
    target_count2 = fields.Integer(string='Target Count 2')
    target_count3 = fields.Integer(string='Target Count 3')
    target_count4 = fields.Integer(string='Target Count 4')
    target_count5 = fields.Integer(string='Target Count 5')
    target_count6 = fields.Integer(string='Target Count 6')
    target_count7 = fields.Integer(string='Target Count 7')
    target_count8 = fields.Integer(string='Target Count 8')
    target_count9 = fields.Integer(string='Target Count 9')
    target_count10 = fields.Integer(string='Target Count 10')
    target_count11 = fields.Integer(string='Target Count 11')
    target_count12 = fields.Integer(string='Target Count 12')
    target_count13 = fields.Integer(string='Target Count 13')
    target_count14 = fields.Integer(string='Target Count 14')
    target_count15 = fields.Integer(string='Target Count 15')
    target_count16 = fields.Integer(string='Target Count 16')
    target_count17 = fields.Integer(string='Target Count 17')
    target_count18 = fields.Integer(string='Target Count 18')
    target_count19 = fields.Integer(string='Target Count 19')
    target_count20 = fields.Integer(string='Target Count 20')
    target_count21 = fields.Integer(string='Target Count 21')
    target_count22 = fields.Integer(string='Target Count 22')
    target_count23 = fields.Integer(string='Target Count 23')
    target_count24 = fields.Integer(string='Target Count 24')
    target_count25 = fields.Integer(string='Target Count 25')
    target_count26 = fields.Integer(string='Target Count 26')
    target_count27 = fields.Integer(string='Target Count 27')
    target_count28 = fields.Integer(string='Target Count 28')
    target_count29 = fields.Integer(string='Target Count 29')
    target_count30 = fields.Integer(string='Target Count 30')

    target_info = fields.Text('Target Information',size=300)
    target_sub_total = fields.Integer(compute='_get_target_allocation_sub_total', string='Total')
        
    
class ward_target_allocation_line(models.Model):
    _name='ward.target.allocation.line'
    _description='State Target Allocation Line'
    
    @api.multi
    @api.onchange('target_count1','target_count2','target_count3','target_count4','target_count5','target_count6','target_count7','target_count8',
                  'target_count9','target_count10','target_count11','target_count12','target_count13','target_count14','target_count15', 'target_count16',
                  'target_count17','target_count18','target_count19','target_count20','target_count21','target_count22','target_count23','target_count24',
                  'target_count25','target_count26','target_count27','target_count28','target_count29','target_count30')
    def _get_target_allocation_sub_total(self):
        for record in self:
            total = 0
            target_info = {}
            for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',record.academic_year_id.id)], order='sequence'):
                target_info.update({target_obj.id:record[(str('target_count')+str(target_obj.sequence+1))]})
                if target_obj.target_type == 'physical':
                    total += record[(str('target_count')+str(target_obj.sequence+1))]
            record.target_info = str(target_info)
            record.target_sub_total = total
    
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    target_allocation_id = fields.Many2one('target.allocation','Target Allocation ID')

    ward_id = fields.Many2one('pappaya.ward', 'Ward', required=True)
    # Fields For Dynamic target column    
    target_count1 = fields.Integer(string='Target Count 1')
    target_count2 = fields.Integer(string='Target Count 2')
    target_count3 = fields.Integer(string='Target Count 3')
    target_count4 = fields.Integer(string='Target Count 4')
    target_count5 = fields.Integer(string='Target Count 5')
    target_count6 = fields.Integer(string='Target Count 6')
    target_count7 = fields.Integer(string='Target Count 7')
    target_count8 = fields.Integer(string='Target Count 8')
    target_count9 = fields.Integer(string='Target Count 9')
    target_count10 = fields.Integer(string='Target Count 10')
    target_count11 = fields.Integer(string='Target Count 11')
    target_count12 = fields.Integer(string='Target Count 12')
    target_count13 = fields.Integer(string='Target Count 13')
    target_count14 = fields.Integer(string='Target Count 14')
    target_count15 = fields.Integer(string='Target Count 15')
    target_count16 = fields.Integer(string='Target Count 16')
    target_count17 = fields.Integer(string='Target Count 17')
    target_count18 = fields.Integer(string='Target Count 18')
    target_count19 = fields.Integer(string='Target Count 19')
    target_count20 = fields.Integer(string='Target Count 20')
    target_count21 = fields.Integer(string='Target Count 21')
    target_count22 = fields.Integer(string='Target Count 22')
    target_count23 = fields.Integer(string='Target Count 23')
    target_count24 = fields.Integer(string='Target Count 24')
    target_count25 = fields.Integer(string='Target Count 25')
    target_count26 = fields.Integer(string='Target Count 26')
    target_count27 = fields.Integer(string='Target Count 27')
    target_count28 = fields.Integer(string='Target Count 28')
    target_count29 = fields.Integer(string='Target Count 29')
    target_count30 = fields.Integer(string='Target Count 30')

    target_info = fields.Text('Target Information',size=300)
    target_sub_total = fields.Integer(compute='_get_target_allocation_sub_total', string='Total')
        
    
    
class area_target_allocation_line(models.Model):
    _name='area.target.allocation.line'
    _description='State Target Allocation Line'
    
    @api.multi
    @api.onchange('target_count1','target_count2','target_count3','target_count4','target_count5','target_count6','target_count7','target_count8',
                  'target_count9','target_count10','target_count11','target_count12','target_count13','target_count14','target_count15', 'target_count16',
                  'target_count17','target_count18','target_count19','target_count20','target_count21','target_count22','target_count23','target_count24',
                  'target_count25','target_count26','target_count27','target_count28','target_count29','target_count30')
    def _get_target_allocation_sub_total(self):
        for record in self:
            total = 0
            target_info = {}
            for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',record.academic_year_id.id)], order='sequence'):
                target_info.update({target_obj.id:record[(str('target_count')+str(target_obj.sequence+1))]})
                if target_obj.target_type == 'physical':
                    total += record[(str('target_count')+str(target_obj.sequence+1))]
            record.target_info = str(target_info)
            record.target_sub_total = total
    
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    target_allocation_id = fields.Many2one('target.allocation','Target Allocation ID')

    area_id = fields.Many2one('pappaya.area', 'Area', required=True)
    # Fields For Dynamic target column    
    target_count1 = fields.Integer(string='Target Count 1')
    target_count2 = fields.Integer(string='Target Count 2')
    target_count3 = fields.Integer(string='Target Count 3')
    target_count4 = fields.Integer(string='Target Count 4')
    target_count5 = fields.Integer(string='Target Count 5')
    target_count6 = fields.Integer(string='Target Count 6')
    target_count7 = fields.Integer(string='Target Count 7')
    target_count8 = fields.Integer(string='Target Count 8')
    target_count9 = fields.Integer(string='Target Count 9')
    target_count10 = fields.Integer(string='Target Count 10')
    target_count11 = fields.Integer(string='Target Count 11')
    target_count12 = fields.Integer(string='Target Count 12')
    target_count13 = fields.Integer(string='Target Count 13')
    target_count14 = fields.Integer(string='Target Count 14')
    target_count15 = fields.Integer(string='Target Count 15')
    target_count16 = fields.Integer(string='Target Count 16')
    target_count17 = fields.Integer(string='Target Count 17')
    target_count18 = fields.Integer(string='Target Count 18')
    target_count19 = fields.Integer(string='Target Count 19')
    target_count20 = fields.Integer(string='Target Count 20')
    target_count21 = fields.Integer(string='Target Count 21')
    target_count22 = fields.Integer(string='Target Count 22')
    target_count23 = fields.Integer(string='Target Count 23')
    target_count24 = fields.Integer(string='Target Count 24')
    target_count25 = fields.Integer(string='Target Count 25')
    target_count26 = fields.Integer(string='Target Count 26')
    target_count27 = fields.Integer(string='Target Count 27')
    target_count28 = fields.Integer(string='Target Count 28')
    target_count29 = fields.Integer(string='Target Count 29')
    target_count30 = fields.Integer(string='Target Count 30')

    target_info = fields.Text('Target Information',size=300)
    target_sub_total = fields.Integer(compute='_get_target_allocation_sub_total', string='Total')
        
class branch_target_allocation_line(models.Model):
    _name='branch.target.allocation.line'
    _description='State Target Allocation Line'
    
    @api.multi
    @api.onchange('target_count1','target_count2','target_count3','target_count4','target_count5','target_count6','target_count7','target_count8',
                  'target_count9','target_count10','target_count11','target_count12','target_count13','target_count14','target_count15', 'target_count16',
                  'target_count17','target_count18','target_count19','target_count20','target_count21','target_count22','target_count23','target_count24',
                  'target_count25','target_count26','target_count27','target_count28','target_count29','target_count30')
    def _get_target_allocation_sub_total(self):
        for record in self:
            total = 0
            target_info = {}
            for target_obj in self.env['marketing.target'].sudo().search([('academic_year_id','=',record.academic_year_id.id)], order='sequence'):
                target_info.update({target_obj.id:record[(str('target_count')+str(target_obj.sequence+1))]})
                if target_obj.target_type == 'physical':
                    total += record[(str('target_count')+str(target_obj.sequence+1))]
            record.target_info = str(target_info)
            record.target_sub_total = total
    
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    target_allocation_id = fields.Many2one('target.allocation','Target Allocation ID')

    branch_id = fields.Many2one('res.company', 'Branch', required=True)
    # Fields For Dynamic target column    
    target_count1 = fields.Integer(string='Target Count 1')
    target_count2 = fields.Integer(string='Target Count 2')
    target_count3 = fields.Integer(string='Target Count 3')
    target_count4 = fields.Integer(string='Target Count 4')
    target_count5 = fields.Integer(string='Target Count 5')
    target_count6 = fields.Integer(string='Target Count 6')
    target_count7 = fields.Integer(string='Target Count 7')
    target_count8 = fields.Integer(string='Target Count 8')
    target_count9 = fields.Integer(string='Target Count 9')
    target_count10 = fields.Integer(string='Target Count 10')
    target_count11 = fields.Integer(string='Target Count 11')
    target_count12 = fields.Integer(string='Target Count 12')
    target_count13 = fields.Integer(string='Target Count 13')
    target_count14 = fields.Integer(string='Target Count 14')
    target_count15 = fields.Integer(string='Target Count 15')
    target_count16 = fields.Integer(string='Target Count 16')
    target_count17 = fields.Integer(string='Target Count 17')
    target_count18 = fields.Integer(string='Target Count 18')
    target_count19 = fields.Integer(string='Target Count 19')
    target_count20 = fields.Integer(string='Target Count 20')
    target_count21 = fields.Integer(string='Target Count 21')
    target_count22 = fields.Integer(string='Target Count 22')
    target_count23 = fields.Integer(string='Target Count 23')
    target_count24 = fields.Integer(string='Target Count 24')
    target_count25 = fields.Integer(string='Target Count 25')
    target_count26 = fields.Integer(string='Target Count 26')
    target_count27 = fields.Integer(string='Target Count 27')
    target_count28 = fields.Integer(string='Target Count 28')
    target_count29 = fields.Integer(string='Target Count 29')
    target_count30 = fields.Integer(string='Target Count 30')

    target_info = fields.Text('Target Information',size=300)
    target_sub_total = fields.Integer(compute='_get_target_allocation_sub_total', string='Total')
