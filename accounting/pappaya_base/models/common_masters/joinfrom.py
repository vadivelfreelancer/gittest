# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class PappayaJoinFrom(models.Model):
    _name = 'pappaya.joinfrom'
    
    school_id = fields.Many2one('operating.unit', 'School', default=lambda self : self.env.user.default_operating_unit_id)
    name = fields.Char(required=1, string='Name', size=40)
    description = fields.Text(string='Description',size=200)
    status = fields.Char('Status')