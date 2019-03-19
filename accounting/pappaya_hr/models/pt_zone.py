# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PappayaPtZone(models.Model):
    _name = 'pappaya.pt.zone'
    _description = 'Pappaya PT Zone'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    
    school_id = fields.Many2one('res.company', 'School', default=lambda self: self.env.user.company_id)
    name = fields.Char(string='Name', size=40)
    account_number = fields.Char(string='Account No.', size=20)
    description = fields.Text(string='Description', size=100)

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")