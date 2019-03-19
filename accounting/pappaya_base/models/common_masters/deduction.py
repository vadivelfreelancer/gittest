# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class PappayaDeduction(models.Model):
    _name = "pappaya.deduction"

    name = fields.Char(string="Name")
    description = fields.Text(string='Description', size=100)

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaDeduction, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaDeduction, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name)])) > 1:
            raise ValidationError("Deduction already exists")

