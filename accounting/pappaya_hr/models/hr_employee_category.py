# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class PappayaEmployeeCategory(models.Model):
    _name = "pappaya.employee.category"

    
    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name','=ilike',self.name)])) > 1:
            raise ValidationError("Category already exists")

    name = fields.Char('Category Name',size=50)
    code = fields.Char(string='Category Code', size=5)
    

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
            res = super(PappayaEmployeeCategory, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaEmployeeCategory, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name


class HrEmployeeSubcategory(models.Model):
    _name = "hr.employee.subcategory"
    
    @api.constrains('name','parent_category_id','code')
    def validate_of_name(self):
        if self.name and self.parent_category_id:
            if len(self.sudo().search([('name','=ilike',self.name),('parent_category_id','=',self.parent_category_id.id)])) > 1:
                raise ValidationError("Sub Category already exists")
        
    name                = fields.Char('Sub Category Name',size=30)
    code                = fields.Char(string='Sub Category Code', size=5)
    parent_category_id  = fields.Many2one('pappaya.employee.category', 'Parent Category')
    is_academic         = fields.Boolean('Is Academic?')     

    
#     @api.onchange('is_academic')
#     def is_academic_onchange(self):
#         for record in self:
#             if record.
#     
    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(HrEmployeeSubcategory, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(HrEmployeeSubcategory, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name




class HrEmployeeCategory(models.Model):
    _inherit = "hr.employee.category"

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(HrEmployeeCategory, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(HrEmployeeCategory, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

