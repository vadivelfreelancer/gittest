# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PappayaEmployeeRelationship(models.Model):
    _name = 'pappaya.employee.relationship'
    _description = 'Pappaya Employee Relationship'
    
    # branch_id = fields.Many2one('res.company', 'Branch', default=lambda self: self.env.user.company_id)
    name = fields.Char(string='Relationship', size=40)

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")

    @api.multi
    def write(self, vals):
        if 'name' in vals:
            raise ValidationError("Sorry, You are not allowed to rename it.\nThis record is considered as master configuration.")


    @api.multi
    def unlink(self):
        for user in self:
            raise ValidationError("Sorry, You are not allowed to delete it.\nThis record is considered as master configuration.")
        return super(PappayaEmployeeRelationship, self).unlink()