# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BranchWiseItemMapping(models.Model):
    _name = 'branch.wise.item.mapping'

    branch = fields.Many2one('operating.unit', 'Branch')
    store_type = fields.Many2one('store.type', string='Store Type')
    item_class = fields.Many2one('pappaya.item.class', string="Item Class")
    item_category = fields.Many2one('product.category', 'Item Category')
