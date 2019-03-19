# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo import tools, api
from odoo.exceptions import ValidationError

class PappayaPackage(models.Model):
    _name = 'pappaya.package'
    _description = 'Pappaya Package'

    name = fields.Char('Package Name', size=124)
    zone_id = fields.Many2one('operating.unit','Zone')
    # office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    branch_id = fields.Many2one('operating.unit','Branch',default=lambda self: self.env.user.default_operating_unit_id)
    description = fields.Text('Description', size=200)
    is_active = fields.Boolean(string='Active', default=True)
    is_bit_sat = fields.Boolean(string='Is Bit Sat', default=False)
    new_commit = fields.Boolean(string='New Commit', default=False)
    new_pak_sno = fields.Integer(string='New Pak SNo.')
    type = fields.Selection([('school', 'School'), ('college', 'College')], string='Type')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaPackage, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaPackage, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name)])) > 1:
            raise ValidationError("Package already exists!")
