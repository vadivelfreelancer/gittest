# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError

class PappayaMandal(models.Model):
    _name = 'pappaya.mandal'
    
    @api.constrains('name')
    def check_name(self):
        if len(self.sudo().search([('name', '=', self.name)]).ids) > 1:
            raise ValidationError("Mandal already exists")
    
    @api.constrains('code')
    def check_code(self):
        if len(self.search([('code', '=', self.code)]).ids) > 1:
            raise ValidationError("Code already exists")
    
    name = fields.Char('Name')
    code = fields.Char()
    pappaya_division_id = fields.Many2one('pappaya.division', string='Division')
    state_district_id = fields.Many2one('state.district', string='District')
    state_id = fields.Many2one('res.country.state', string="State")
    
    @api.onchange('pappaya_division_id')
    def _onchange_pappaya_division_id(self):
        if self.pappaya_division_id:
            self.state_district_id = self.pappaya_division_id.state_district_id.id
            self.state_id = self.pappaya_division_id.state_id.id

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaMandal, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaMandal, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name
            