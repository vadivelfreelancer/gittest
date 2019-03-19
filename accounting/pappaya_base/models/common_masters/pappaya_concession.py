# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class PappayaConcession(models.Model):
    _name = 'pappaya.concession'
    _description = 'Pappaya Concession'

    name = fields.Char(string='Name', size=40)
    description = fields.Text(string='Description', size=100)
    is_active = fields.Boolean(string='Active', default=True)
    school_id = fields.Many2one('operating.unit', 'Branch', default=lambda self: self.env.user.default_operating_unit_id)
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))