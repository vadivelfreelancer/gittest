# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SubCategoryWithSubLedger(models.Model):
    _name = 'subcategory.with.subledger'

    sub_ledger = fields.Char('Sub Ledger', size=20)
    revenue_capital = fields.Char('Revenue/Capital')
