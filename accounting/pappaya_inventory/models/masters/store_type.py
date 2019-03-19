# -*- coding: utf-8 -*-
from odoo import models, fields


class StoreType(models.Model):
    _name = 'store.type'

    name = fields.Char('Store Type', size=20)
