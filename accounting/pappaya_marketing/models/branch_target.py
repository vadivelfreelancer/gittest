# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class BranchTarget(models.Model):
    _name = 'pappaya.branch.target'
    _description='Branch Target Entry'
    _rec_name = 'academic_year_id'
    
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    school_id = fields.Many2many('res.company', 'res_company_id', 'branches_target_id', string="Branches")
    state_id = fields.Many2one('res.country.state', string='State', domain=[('country_id.is_active', '=', True)])
    district_id = fields.Many2many('state.district', 'branches_relation_id', 'branches_target_id', string='District')
    lock_unlock = fields.Selection([('unlock', 'Unlock'), ('lock', 'Lock')], string="Lock/Unlock")
    branches = fields.Selection([('school', 'School'), ('college', 'College')], string="School/College")
    course_packages_ids = fields.One2many('pappaya.branch.target.line', 'branch_course_id')
    
    @api.multi
    @api.onchange('state_id')
    def load_district(self):
        if self.state_id:
            list_district = []
            districts = self.env['state.district'].search([('state_id', '=', self.state_id.id)])
            for dist in districts:
                list_district.append(dist.id)
                
            self.district_id = list_district
            branch_list = []
            for b in list_district:
                 
                division_ids = self.env['pappaya.division'].search([('state_district_id', '=', b)])
                for div in division_ids:
                    manadal_ids = self.env['pappaya.mandal'].search([('pappaya_division_id', '=', div.id)])
                    
                    for mand in manadal_ids:
                        branch_list_ids = self.env['res.company'].search([('pappaya_mandal_id', '=', mand.id)])
                        for b in branch_list_ids:
                            branch_list.append(b.id)
                            
                        self.school_id = branch_list
                        
    @api.multi
    @api.onchange('district_id')
    def onchange_district_id(self):
        self.school_id = False
        if self.district_id:
            branch_list = []
            for b in self.district_id.ids:
                division_ids = self.env['pappaya.division'].search([('state_district_id', '=', b)])
                for div in division_ids:
                    manadal_ids = self.env['pappaya.mandal'].search([('pappaya_division_id', '=', div.id)])
                    for mand in manadal_ids:
                        branch_list_ids = self.env['res.company'].search([('pappaya_mandal_id', '=', mand.id)])
                        for b in branch_list_ids:
                            branch_list.append(b.id)
            self.school_id = branch_list                        

    @api.multi
    def collect_branch_course(self):
        if not self.course_packages_ids:
            if self.school_id:
                for cb in self.school_id:
                    
                    for course_line in cb.course_config_ids:
                        if course_line.active and self.academic_year_id.id == course_line.academic_year_id.id:
                            for co in course_line.course_package_ids:
                               
                                for line in co:
                                    self.env['pappaya.branch.target.line'].create({'course_id':line.id,
                                                                                   'branch_course_id':self.id,
                                                                                   'branch_id':cb.id})    
class PappayaBranchLine(models.Model):
    _name = 'pappaya.branch.target.line'
    _description='Branch Target Line'
    
    branch_course_id = fields.Many2one('pappaya.branch.target')
    course_id = fields.Many2one('pappaya.course.package')
    branch_id = fields.Many2one('res.company')
    res_target = fields.Integer(string="Res Target")
    adm_target = fields.Integer(string="Adm Target")
    lock_unlock = fields.Boolean(srting="Lock/Unlock")
