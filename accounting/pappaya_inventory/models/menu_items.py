# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Menu(models.Model):
    _name = 'menu.items.master'
    _rec_name = 'menu_items'

    menu_items = fields.Char('Menu Item', size=40)
    status = fields.Selection([('active', 'ACTIVE'), ('inactive', 'IN ACTIVE')], default='active', string='Status')
