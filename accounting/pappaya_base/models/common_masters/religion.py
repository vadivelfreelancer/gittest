# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PappayaReligion(models.Model):
    _name = 'pappaya.religion'
    
    school_id = fields.Many2one('operating.unit', 'School', default=lambda self : self.env.user.default_operating_unit_id)
    name = fields.Char(required=1, size=40)
    religion_code = fields.Char(string='Religion Code',size=20)

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaReligion, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaReligion, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.multi
    def _check_religion(self):
        exiting_ids = self.search([('name', '=', self.name)])
        if len(exiting_ids) > 1:
            return False
        return True

    @api.multi
    def _check_religion_code(self):
        exiting_ids = self.search([('religion_code', '=', self.religion_code)])
        if len(exiting_ids) > 1:
            return False
        return True

    _constraints = [(_check_religion, 'Religion name already exists', ['name']),
                    (_check_religion_code, 'Religion Code already exists', ['religion_code'])]
