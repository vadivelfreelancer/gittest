# -*- coding: utf-8 -*-
# Copyright (C) 2017-present  Technaureus Info Solutions(<http://www.technaureus.com/>).
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 
                 'currency_id', 'company_id', 'date_invoice')
    def _compute_amount(self):
        res = super(AccountInvoice, self)._compute_amount()
        self.amount_tax = sum(line.amount for line in self.tax_line_ids if not line.tds)
        self.tds_amt = sum(line.amount for line in self.tax_line_ids if line.tds)
        self.total_gross = self.amount_untaxed + self.amount_tax
        self.amount_total = self.amount_untaxed + self.amount_tax + self.tds_amt
        return res
    
    tds = fields.Boolean('Apply TDS', default=False, readonly=True, 
                         states={'draft': [('readonly', False)]})
    tds_tax_id = fields.Many2one('account.tax', string='TDS', readonly=True, 
                                 states={'draft': [('readonly', False)]})
    tds_amt = fields.Monetary(string='TDS Amount',
        store=True, readonly=True, compute='_compute_amount')
    total_gross = fields.Monetary(string='Total',
        store=True, readonly=True, compute='_compute_amount')
    amount_total = fields.Monetary(string='Net Total',
        store=True, readonly=True, compute='_compute_amount')
    vendor_type = fields.Selection(related='partner_id.company_type', string='Partner Type')
    
    @api.multi
    def get_taxes_values(self):
        res = super(AccountInvoice, self).get_taxes_values()
        tax_obj = self.env['account.tax']
        for tax_line in res.keys():
            if res[tax_line] and res[tax_line]['tax_id']:
                tax = tax_obj.browse(res[tax_line]['tax_id'])
                if tax.tds:
                    res[tax_line]['tds'] = True
                    res[tax_line]['amount'] = - res[tax_line]['amount']
                else:
                    res[tax_line]['tds'] = False
        return res
    
    def check_turnover(self, partner_id, threshold, total_gross):
        domain = [('partner_id','=',partner_id),('account_id.internal_type', '=', 'payable'),
                  ('move_id.state','=','posted'), ('account_id.reconcile','=',True)]
        journal_items = self.env['account.move.line'].search(domain)
        credits = sum([item.credit for item in journal_items])
        credits += total_gross
        if credits >= threshold:
            return True
        else:
            return False
    
    @api.multi
    def update_tds(self):
        for invoice in self:
            applicable = True
            if invoice.partner_id and invoice.partner_id.tds_threshold_check:
                applicable = self.check_turnover(invoice.partner_id.id, invoice.tds_tax_id.payment_excess, invoice.total_gross)
            tds_sum = 0
            for line in invoice.invoice_line_ids:
                for tax in line.invoice_line_tax_ids:
                    if tax.tds:
                        line.invoice_line_tax_ids = ([(2, tax.id)])
                if applicable:
                    line.invoice_line_tax_ids = ([(4, invoice.tds_tax_id.id)])
            invoice._onchange_invoice_line_ids()
        return True
    
    @api.multi
    def clear_tds(self):
        for invoice in self:
            invoice.tds = False
            invoice.tds_tax_id = False
            invoice.tds_amt = 0
            for line in invoice.invoice_line_ids:
                for tax in line.invoice_line_tax_ids:
                    if tax.tds:
                        line.invoice_line_tax_ids = ([(2, tax.id)])
            for tax_line in invoice.tax_line_ids:
                if tax_line.tds:
                    tax_line.unlink()
        return True
            
class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"
    
    tds = fields.Boolean('TDS', default=False)
    