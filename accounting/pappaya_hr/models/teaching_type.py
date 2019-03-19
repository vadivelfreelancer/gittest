# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class PappayaTeachingType(models.Model):
    _name = 'pappaya.teaching.type'
    _inherit = ['mail.thread']
    _mail_post_access = 'read'
    
    school_id = fields.Many2one('res.company', 'School', default=lambda self : self.env.user.company_id)
    name = fields.Char(required=1, string='Name', size=40)
    code = fields.Char(string='Code', size=5)
    description = fields.Text(string='Description', size=100)

    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=', self.name)])) > 1:
            raise ValidationError("Name already exists")