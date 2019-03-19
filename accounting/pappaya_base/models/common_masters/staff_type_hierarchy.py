# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError

class StaffTypeHierarchy(models.Model):
    _name='staff.type.hierarchy'
    _description='Staff Type Hierarchy'
    _rec_name = 'job_id'

    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char('Name',size=150)
    academic_type = fields.Selection([('academic','Academic'),('non_academic','Non Academic')], string='Academic Type', default='academic')
    job_id = fields.Many2one('hr.job', 'Job Position')
    parent_id = fields.Many2one('staff.type.hierarchy', 'Head')
    is_head = fields.Boolean('Is Head')
    description = fields.Text('Description',size=200)
    
    @api.onchange('job_id')
    def onchange_job_id(self):
        if self.job_id:
            self.name = self.job_id.name

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(StaffTypeHierarchy, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(StaffTypeHierarchy, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name)])) > 1:
            raise ValidationError("Staff Type already exists")
    
class ProgramType(models.Model):
    _name='program.type'
    _description='Program Type'
    
    name = fields.Char('Name' ,size=150)
    description = fields.Text('Description' ,size=200)

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(ProgramType, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(ProgramType, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name)])) > 1:
            raise ValidationError("Program Type already exists")
    