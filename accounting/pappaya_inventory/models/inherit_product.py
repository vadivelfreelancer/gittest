# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class InheritProduct(models.Model):
    _inherit = 'product.product'

    store_type = fields.Many2one('store.type', string='Store Type')
    item_class = fields.Many2one('pappaya.item.class', 'Item Class')
    is_special_track = fields.Boolean('Is Special Track')
    is_expire = fields.Boolean('Is Expire')
    is_return_to_vendor = fields.Boolean('Is Return To Vendor')
    is_asset = fields.Boolean('Is Asset')
    is_consumable = fields.Boolean('Is Consumable')


