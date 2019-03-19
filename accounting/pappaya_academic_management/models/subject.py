# -*- coding: utf-8 -*-
from odoo import models, fields


class PappayaSubject(models.Model):
    _inherit = 'pappaya.subject'

    institution_type = fields.Selection([('college', 'College'), ('school', 'School')], string="Type")
