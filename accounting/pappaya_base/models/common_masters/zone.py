# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo import tools, api
from odoo.exceptions import ValidationError


class PappayaZone(models.Model):
    _name = 'pappaya.zone'

    name = fields.Char('Name', size=124)
    description = fields.Text('Description' ,size=200)
    user_slno = fields.Char('User SL No.',size=20)
    ip_address = fields.Char('IP Address',size=20)
    zone_code = fields.Char('Zone Code',size=6)
    col_daystn = fields.Char('Col Days TN',size=20)
    col_hosttn = fields.Char('Col Host TN',size=20)
    schl_daystn = fields.Char('Sch Days TN',size=20)
    schl_hosttn = fields.Char('Sch Host TN',size=20)

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaZone, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaZone, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name)])) > 1:
            raise ValidationError("Zone already exists")
