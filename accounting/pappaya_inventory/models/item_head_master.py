# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ItemHeadMaster(models.Model):
    _name = 'item.head.master'
    _rec_name = 'name'

    name = fields.Char('Name', size=20)
    description = fields.Char('Description')
    status = fields.Selection([('active', 'Active'), ('inactive', 'In Active')], 'Status')
