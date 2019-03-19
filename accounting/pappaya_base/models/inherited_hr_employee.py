# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    entry_type = fields.Selection([('agm','AGM'),('dgm','DGM'),('gm','GM'),('ao','AO'),('dean','Dean'),
                                   ('principal','Principal'),('incharge','Incharge')], string="Entry Type")