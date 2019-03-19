# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import ValidationError


class RecruitmentDocument(models.Model):
    _name = "recruitment.document"

    name = fields.Char(string="Name",size=30)
    description = fields.Text(string='Description',size=200)


    @api.constrains('name')
    def validate_of_name(self):
        if len(self.sudo().search([('name', '=', self.name)])) > 1:
            raise ValidationError("Document already exists")

