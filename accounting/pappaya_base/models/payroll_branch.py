# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re

class residential_type(models.Model):
    _name='residential.type'
    _description='Residential Type'

    name = fields.Char('Name')
    code = fields.Char('Code')
    
class pappaya_gender(models.Model):
    _name='pappaya.gender'
    _description='Gender'
    
    name = fields.Char('Gender',size=10)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name_lower = str(self.name.strip()).lower()
            name = self.env['res.company']._validate_name(name_lower)
            self.name = name

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Gender already exists")

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            raise ValidationError("Sorry, You are not allowed to rename it.\nThis record is considered as master configuration.")


    
class branch_type(models.Model):
    _name='branch.type'
    _description='School/College'
    
    name=fields.Char('Name')


class statutory_requirment(models.Model):
    _name = 'statutory.requirment'
    _description = 'Statutory'

    name = fields.Char('Statutory Name',size=30)
    description = fields.Char('Description', size=100)


class PayrollBranch(models.Model):
    _name='pappaya.payroll.branch'
    _description='Payroll Branch'
    
    name = fields.Char('Name')
    office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    branch_type = fields.Selection([('school','School'),('college','College')], 'Branch Type')
    state_id = fields.Many2one('res.country.state','State', domain=[('country_id.is_active','=',True)])
    record_id = fields.Integer('ID')
    emp_no_ref = fields.Char('Created Employee ID')
    description = fields.Text('Description',size=200)
    
    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name
        
    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PayrollBranch, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        return super(PayrollBranch, self).write(vals)
    
    @api.constrains('name','office_type_id','state_id','record_id')
    def validate_duplicate(self):
        if self.sudo().search_count([('name','=',self.name),('office_type_id','=',self.office_type_id.id),('state_id','=',self.state_id.id)]) > 1:
            raise ValidationError("Record already exists for given name, Office type and state")
        if self.record_id and self.record_id > 0 and self.sudo().search_count([('record_id','=',self.record_id)]) > 1:
            raise ValidationError("Record already exists for given record ID")