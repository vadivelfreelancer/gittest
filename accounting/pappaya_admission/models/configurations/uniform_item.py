# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class PappayaUniformItem(models.Model):
    _name = 'pappaya.uniform.item'
    _description = 'Pappaya Uniform Item'

    name = fields.Char(string='Name', size=40)
    status = fields.Char(string='Status', size=5)
    user_sl_no = fields.Integer(string='User SL No.')
    is_active = fields.Boolean(string='Active', default=True)
    school_id = fields.Many2one('operating.unit', 'Branch')# default=lambda self: self.env.user.company_id)
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))