# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BranchWiseItemCategoryMapping(models.Model):
    _name = 'branch.wise.item.category.mapping'
    _rec_name = 'branch'

    branch = fields.Many2one('operating.unit', 'Branch')
    item_category = fields.Many2one('product.category', 'Item Category')
    status = fields.Selection([('active', 'Active'), ('inactive', 'In Active')], 'Status')

