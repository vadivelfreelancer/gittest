# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TaxUpdateMaster(models.TransientModel):
    _name = 'tax.update.master'

    item_class = fields.Many2one('pappaya.item.class', 'Item Class')
    item_category = fields.Many2one('pappaya.item.category', 'Item Category')
    item_sub_category = fields.Many2one('pappaya.item.subcategory', 'Item Sub Category')
    item_master_ids = fields.Many2one('pappaya.item.master','Item Master')
    taxes_id = fields.Many2many('account.tax', 'product_taxes_rel', 'prod_id', 'tax_id', string='Customer Taxes',
                                domain=[('type_tax_use', '=', 'sale')])

    @api.onchange('item_class')
    def _onchange_item_class(self):
        if self.item_class:
            category = self.env['pappaya.item.category'].search([('item_class', '=', self.item_class.id)]).ids
            subcategory = self.env['pappaya.item.subcategory'].search([('item_category', 'in', category)]).ids
            itemmaster = self.env['pappaya.item.master'].search([('item_sub_category', 'in', subcategory)]).ids
        else:
            category = self.env['pappaya.item.category'].search([]).ids
            subcategory = self.env['pappaya.item.subcategory'].search([]).ids
            itemmaster = self.env['pappaya.item.master'].search([]).ids
        return {'domain': {'item_category': [('id', 'in', category)],'item_sub_category': [('id', 'in', subcategory)],
                           'item_master_ids': [('id', 'in', itemmaster)]}}

    @api.onchange('item_category')
    def _onchange_item_category(self):
        if self.item_category:
            subcategory = self.env['pappaya.item.subcategory'].search([('item_category', '=', self.item_category.id)]).ids
            itemmaster = self.env['pappaya.item.master'].search([('item_sub_category', 'in', subcategory)]).ids
        else:
            subcategory = self.env['pappaya.item.subcategory'].search([]).ids
            itemmaster = self.env['pappaya.item.master'].search([]).ids
        return {'domain': {'item_sub_category': [('id', 'in', subcategory)],'item_master_ids': [('id', 'in', itemmaster)]}}

    @api.onchange('item_sub_category')
    def _onchange_item_sub_category(self):
        if self.item_sub_category:
            itemmaster = self.env['pappaya.item.master'].search([('item_sub_category', '=', self.item_sub_category.id)]).ids
        else:
            itemmaster = self.env['pappaya.item.master'].search([]).ids
        return {'domain': {'item_master_ids': [('id', 'in', itemmaster)]}}

    @api.multi
    def action_update_tax(self):
        print(self.item_master_ids)
        for record in self.item_master_ids:
            print (record)
            record.taxes_id = self.taxes_id
        return True

