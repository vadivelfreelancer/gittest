# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class PappayaVehicle(models.Model):
    _name = 'pappaya.vehicle'
    _description = 'Pappaya vehicle'

    @api.constrains('name','registration_no')
    def check_name(self):
        if self.name:
            if len(self.search([('school_id', '=', self.school_id.id),('name', '=', self.name)])) > 1:
                raise ValidationError("Name already exists.")
        if self.registration_no:
            if len(self.search([('registration_no', '=', self.registration_no)])) > 1:
                raise ValidationError("Registration No. already exists.")

    @api.constrains('seating_capacity')
    def _check_seating_capacity(self):
        for i in self.seating_capacity:
            if i.isalpha():
                raise ValidationError("Enter Valid Seating Capacity")
        if int(self.seating_capacity) <= 0 or int(self.seating_capacity) > 100:
            raise ValidationError("Seating Capacity must be positive or greater than zero")

    @api.constrains('per_month_amount')
    def _check_per_amount(self):
        if self.per_month_amount <= 0:
            raise ValidationError("Please enter the valid amount..!")

    name = fields.Char(string='Name', size=40)
    registration_no = fields.Char(string='Registration No.', size=40)
    seating_capacity = fields.Char(string='Seating Capacity',size=3)
    per_month_amount = fields.Float(string='Per Month Amount')
    description = fields.Text(string='Description', size=100)
    is_active = fields.Boolean(string='Active', default=True)
    school_id = fields.Many2one('operating.unit', 'Branch')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    transport_type_id = fields.Many2one('pappaya.master', string='Vehicle Type')
    transport_incharge_ids = fields.Many2many('hr.employee', string='Transport In charge', domain=[('id', '!=', 1)])

    @api.onchange('school_id')
    def onchange_school(self):
        if self.school_id:
            self.transport_incharge_ids = None
            
