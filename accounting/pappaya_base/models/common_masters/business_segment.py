# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class BusinessSegment(models.Model):
    _name = 'pappaya.business.segment'


    name = fields.Char(required=1, string='Business Segment Name', size=40)
    description = fields.Text(string='Description', size=100)


    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")

