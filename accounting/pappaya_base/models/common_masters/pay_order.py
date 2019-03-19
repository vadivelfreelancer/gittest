# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PappayaPayOrder(models.Model):
    _name = 'pappaya.pay.order'
    _description = 'Pappaya Pay Order'

    name = fields.Char(string='Name', size=40)
    pay_mode_type = fields.Char(string='Pay Mode Type', size=40)
    description = fields.Text(string='Description', size=100)
    is_active = fields.Boolean(string='Active', default=True)
    is_dependent = fields.Boolean(string='Is Dependent', default=False)
    is_cheque = fields.Boolean(string='Is Cheque', default=False)
    school_id = fields.Many2one('operating.unit', 'Branch', default=lambda self: self.env.user.default_operating_unit_id)
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")