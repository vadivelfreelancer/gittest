# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MenuMasterMapping(models.Model):
    _name = 'menu.master.mapping'
    _rec_name = 'menu'

    menu = fields.Many2one('menu.master', 'Menu')
    menu_items = fields.Many2one('menu.items.master', 'Menu Item')

