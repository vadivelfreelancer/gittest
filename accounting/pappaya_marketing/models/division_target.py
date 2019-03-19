# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import re


class DivisionInherit(models.Model):
    _inherit = 'pappaya.division'
    _description = "Narayana Division"

    mandal_ids_m2m = fields.Many2many('pappaya.mandal.marketing', string="Mandals")