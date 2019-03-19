# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ItemHeadWithUserMapping(models.Model):
    _name = 'item.head.user.mapping'

    item_head = fields.Many2one('item.head.master', 'Item Head')
    user_category = fields.Char('User Category', size=15)
