# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PappayaItemClass(models.Model):
    _name = 'pappaya.item.class'
    _rec_name = 'item_class'

    item_class = fields.Char('Item Class', size=80)
    item_class_code = fields.Char('Item Class Code', size=20)
    store_type = fields.Many2one('store.type', string='Store Type')
    description = fields.Char('Description')

    @api.constrains('item_class')
    def check_item_class(self):
        if len(self.search([('item_class', '=', self.item_class)])) > 1:
            raise ValidationError("Item class already exists")

    @api.onchange('item_class', 'item_class_code')
    def check_strip(self):
        if self.item_class:
            self.item_class = self.item_class.strip()
        if self.item_class_code:
            self.item_class_code = self.item_class_code.strip()

    @api.multi
    def name_get(self):
        res = super(PappayaItemClass, self).name_get()
        result = []
        if self._context.get('itemclass') == 'item_class':
            for mg in self:
                print(self._context)
                result.append((mg.id, mg.item_class_code))
            return result
        return res
