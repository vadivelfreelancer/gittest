# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class Pappayacluster(models.Model):
    _name = "pappaya.cluster"
    _description='Cluster'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    
    name = fields.Char('Cluster' ,size=150)
    description = fields.Text(string="Description", size=100)
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", required=1, default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    state_ids_m2m = fields.Many2many('res.country.state', string='States')
    district_ids_m2m = fields.Many2many('state.district', string="Districts")

    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(Pappayacluster, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(Pappayacluster, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name

    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name),('academic_year_id','=',self.academic_year_id.id)])) > 1:
            raise ValidationError("Cluster already exists")