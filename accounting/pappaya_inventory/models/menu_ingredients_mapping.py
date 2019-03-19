# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MenuMasterMapping(models.Model):
    _name = 'menu.ingredients.mapping'
    _rec_name = 'menu'

    menu = fields.Many2one('menu.master', 'Menu')
    menu_items = fields.Many2one('menu.items.master', 'Menu Item')
    ingredient_item = fields.Char('Ingredient Item', size=20)
    per_members = fields.Integer('Per Members', size=8)
    ingredient_item_qty = fields.Integer('Ingredient Item Qty')
