# -*- coding: utf-8 -*-
from odoo import models, fields


class BranchMenuItemsMapping(models.Model):
    _name = 'branch.menuitems.mapping'
    _rec_name = 'branch'

    branch = fields.Many2one('operating.unit', 'Branch')
    menu = fields.Many2one('menu.master', 'Menu')
    menu_items = fields.Many2one('menu.items.master', 'Menu Item')


