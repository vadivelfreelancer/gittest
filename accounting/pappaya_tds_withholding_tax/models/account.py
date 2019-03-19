# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).
from odoo import api, fields, models, _

class AccountTax(models.Model):
    _inherit = 'account.tax'
    
    tds = fields.Boolean('TDS', default=False)
    payment_excess = fields.Float('Payment in excess of')
    tds_applicable = fields.Selection([('person','Individual'),
                                 ('company','Company'),
                                 ('common','Common')], string='Applicable to')