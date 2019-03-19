# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DailyMenuConsumption(models.Model):
    _name = 'daily.menu.consumption'

    branch = fields.Many2one('operating.unit', 'Branch(Kitchen Point)')
    date = fields.Date('Date', default=fields.Date.today)
    menu = fields.Many2one('menu.master', 'Menu')
    total_studednts = fields.Integer('Total Students', size=4)
    menu_items = fields.Many2one('menu.items.master', 'Menu Item')
    no_of_members = fields.Integer('No. Of Members', size=4)
