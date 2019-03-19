# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PappayaLeadCourse(models.Model):
    _name = 'pappaya.lead.course'
    _order='name asc'
    
    record_id = fields.Integer('ID')
    name = fields.Char(string="Name" ,size=150)
    description = fields.Char(string="Description",size=150)

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaLeadCourse, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PappayaLeadCourse, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name)]).ids) > 1:
            raise ValidationError("Lead Course already exists")
        
    @api.constrains('record_id')
    def validate_of_record_id(self):
        # if self.record_id == 0:
        #     raise ValidationError("ID should not be 0.")
        if len(self.sudo().search([('record_id', '=', self.record_id)]).ids) > 1:
            raise ValidationError("ID already exists.")