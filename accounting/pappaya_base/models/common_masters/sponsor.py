# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class PappayaSponsor(models.Model):
    _name = 'pappaya.sponsor'
    
    school_id = fields.Many2one('operating.unit', 'Branch', default=lambda self : self.env.user.default_operating_unit_id)
    academic_year_id = fields.Many2one('academic.year', 'Academic Year',default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    name = fields.Char(string='Name', size=40)
    sponsor_type_id = fields.Many2one('pappaya.master', string='Sponsor Type')
    description = fields.Text(string='Description' ,size=200)
    status = fields.Char('Status')
    amount = fields.Float('Amount')

    street = fields.Char('Street',size=100)
    street2 = fields.Char('Street2',size=100)
    zip = fields.Char('Pin Code', size=6)
    city = fields.Char('City',size=20)
    state_id = fields.Many2one("res.country.state", 'State', domain=[('country_id.is_active', '=', True)])
    country_id = fields.Many2one("res.country", 'Country', domain=[('is_active', '=', True)], default=lambda self: self.env.user.company_id.country_id)
    sponsor_doc_ids = fields.One2many('pappaya.workflow.sponsorconfig', 'sponsor_id', 'Sponsor Document')

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name),('school_id', '=', self.school_id.id)])) > 1:
            raise ValidationError("Name already exists")


class PappayaWorkflowSponsorDocConfig(models.Model):

    _name = "pappaya.workflow.sponsorconfig"
    _order = "id asc"
    _description = "Sponsor Document Config"

    document_name = fields.Char('Document Name',size=100)
    sponsor_id = fields.Many2one('pappaya.sponsor', string='Sponsor')
    description = fields.Char('Description',size=100)
    required = fields.Boolean('Required')