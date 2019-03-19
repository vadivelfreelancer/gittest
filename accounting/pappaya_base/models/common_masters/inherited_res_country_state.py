# -*- coding: utf-8 -*-
import re
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ResCountryState(models.Model):
    _inherit = "res.country.state"
    _order = 'name asc'
    
    @api.constrains('name')
    def check_name(self):
        if self.name:
            if len(self.sudo().search([('name', '=', self.name)]).ids) > 1:
                raise ValidationError("State already exists.")
    
    @api.constrains('code','country_id')
    def check_code(self):
        if self.code and self.country_id:
            if not re.match(r'^[A-Za-z]+$', self.code):
                raise ValidationError('Please enter valid code.')
            if len(self.search([('code', '=', self.code),('country_id','=',self.country_id.id)]).ids) > 1:
                raise ValidationError("Code and country should be unique.")

    @api.constrains('sequence')
    def check_sequence(self):
        if self.sequence < 0:
            raise ValidationError("Sequence should not be Negative (-ve)")
        if self.sequence == 0:
            raise ValidationError("Sequence should not be Zero '0'")
    
    @api.constrains('record_id')
    def check_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")

    @api.onchange('sequence')
    def onchange_sequence(self):
        self.check_sequence()

    record_id = fields.Integer('ID')
    sequence = fields.Integer(string='Sequence')
    state_code_phone = fields.Char('State Calling Code', size=5)
    country_id = fields.Many2one('res.country', 'Country', required=True, domain=[('is_active','=',True)], default=lambda self: self.env.user.company_id.country_id)
    sequence_id = fields.Char('Series',size=20)
    name = fields.Char(string='State Name', required=True,
               help='Administrative divisions of a country. E.g. Fed. State, Departement, Canton',size=30)
    code = fields.Char(string='State Code', help='The state code.', required=True, size=5)
 
    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
            res = super(ResCountryState, self).create(vals)
            sequence_config =self.env['meta.data.master'].search([('name','=','state')])
            if not sequence_config:
                raise ValidationError("Please Configure State Sequence")
            res['sequence_id'] = self.env['ir.sequence'].next_by_code('pappaya.state') or _('New')
        return res

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(ResCountryState, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name
            
    @api.onchange('sequence')
    def onchange_sequence(self):
        if self.sequence < 0:
            raise ValidationError('Please enter the valid Sequence..!')  

    @api.onchange('code')
    def onchange_code(self):
        self.check_code()