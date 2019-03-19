# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class StateDistrict(models.Model):
    _name = "state.district"
    _order='name asc'
    
    # @api.constrains('name','code','state_id')
    # def check_code(self):
    #     if len(self.search([('code', '=', self.code),('state_id','=',self.state_id.id)])) > 1:
    #         raise ValidationError("The code of the district must be unique by state !")
        
    @api.constrains('record_id')
    def validate_of_record_id(self):
        if self.record_id > 0 and len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")
        
    record_id = fields.Integer('ID')
    name = fields.Char("District Name",size=150)
    code = fields.Char('District Code',size=100)
    district_code = fields.Char(size=10)
    state_id = fields.Many2one('res.country.state', string="State", domain=[('country_id.is_active','=',True)])
    country_id = fields.Many2one('res.country', string="Country", domain=[('is_active','=',True)], default=lambda self: self.env.user.company_id.country_id)
    description = fields.Text(string='Description', size=100)
    ip_address = fields.Char('IP Address',size=20)
    ap_nonap = fields.Char('AP Non AP',size=20)
    area_slno = fields.Char('Area Sl No.',size=20)
    is_feelock = fields.Boolean("Is Feelock")
    short_name = fields.Char('Short Name' ,size=100)
    short_name1 = fields.Char('Short Name 1',size=100)
    is_update = fields.Boolean("Is update")

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(StateDistrict, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(StateDistrict, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.onchange('code')
    def onchange_code(self):
        if self.code:
            code = self.env['res.company']._validate_name(self.code)
            self.code = code

    @api.constrains('name', 'state_id', 'code')
    def validate_of_name(self):
        if self.name and self.code and self.state_id:
            if len(self.sudo().search([('name', '=', self.name), ('state_id', '=', self.state_id.id), ('code', '=', self.code)]).ids) > 1:
                raise ValidationError("District already exists")
        if self.code:
            if len(self.sudo().search([('code', '=', self.code)]).ids) > 1:
                raise ValidationError("District Code already exists")
        if self.name and self.state_id:
            if len(self.sudo().search([('name', '=', self.name),('state_id', '=', self.state_id.id)]).ids) > 1:
                raise ValidationError("District Name Already Exists For This State")