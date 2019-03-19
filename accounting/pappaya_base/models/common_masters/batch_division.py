# -*- coding: utf-8 -*-
from odoo import models, fields,api
from odoo.exceptions import ValidationError


class PappayaBatchDivision(models.Model):
    _name = 'pappaya.batch.division'

    name = fields.Char('Name', size=124)    
    academic_year = fields.Many2one('academic.year','Academic Year',default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    zone_id = fields.Many2one('operating.unit','Zone')
    branch_id = fields.Many2one('operating.unit','Branch')
    description = fields.Text('Description',size=200)
    batch_id = fields.Many2one('pappaya.batch',string='Batch')

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaBatchDivision, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaBatchDivision, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name)])) > 1:
            raise ValidationError("Batch Division already exists")
