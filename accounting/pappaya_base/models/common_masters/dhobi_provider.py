# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PappayaDhobiType(models.Model):
    _name = 'pappaya.dhobi.provider'

    school_id = fields.Many2one('operating.unit', string='Branch')
    name = fields.Char(required=1, string='Name', size=40)
    street = fields.Char(string='Street', size=25)
    street2 = fields.Char(string='Street2', size=25)
    city = fields.Char(string='City', size=20)
    state_id = fields.Many2one('res.country.state', string='State')
    district_id = fields.Many2one('state.district', string='District')
    country_id = fields.Many2one('res.country', string='Country',
                                 default=lambda self: self.env.user.company_id.country_id)
    zip = fields.Char(string='Zip', size=6)
    mobile_1 = fields.Char(string='Mobile', size=10)
    mobile_2 = fields.Char(string="Alternate Mobile", size=10)
    pickup_date = fields.Date(string='Pickup Date')
    delivery_date = fields.Date(string='Delivery Date')
    head_count = fields.Integer(string='Head Count')
    used_count = fields.Integer(string='Used Count')
    opinion = fields.Selection([('poor', 'Poor'), ('average', 'Average'), ('good', 'Good'), ('excellent', 'Excellent')],
                               string='Opinion')
    remarks = fields.Char(string='Remarks', size=100)

    @api.onchange('head_count', 'used_count')
    def onchange_count(self):
        if self.head_count < 0 or self.used_count < 0:
            raise ValidationError('Please enter Valid Count')

    @api.onchange('pickup_date', 'delivery_date')
    def onchange_dates(self):
        self.check_dates()

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")

    @api.constrains('zip')
    def check_zip(self):
        if self.zip:
            self.env['res.company'].validate_zip(self.zip)

    @api.constrains('mobile_1')
    def check_mobile_1(self):
        if self.mobile_1:
            self.env['res.company'].validate_mobile(self.mobile_1)

    @api.constrains('mobile_2')
    def check_mobile_2(self):
        if self.mobile_2:
            self.env['res.company'].validate_mobile(self.mobile_2)

    @api.constrains('pickup_date', 'delivery_date')
    def check_dates(self):
        if self.pickup_date and self.delivery_date:
            if self.delivery_date < self.pickup_date:
                raise ValidationError('Pickup Date should be less than Delivery Date..!')
