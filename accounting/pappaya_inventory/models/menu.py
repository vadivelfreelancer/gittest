# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Menu(models.Model):
    _name = 'menu.master'
    _rec_name = 'menu'

    menu = fields.Char('Menu', size=20)
    status = fields.Selection([('active', 'ACTIVE'), ('inactive', 'IN ACTIVE')], default='active', string='Status')
