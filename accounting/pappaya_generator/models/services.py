from odoo import models, fields, api

month_list = [(1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),(5, 'May'), (6, 'June'), (7, 'July'),
              (8, 'August'), (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')]

class Services(models.Model):
    _name = 'service.details'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    building_id = fields.Many2one('pappaya.building', string='Building Name', required=True,
                                  domain="[('branch_id', '=', branch_id)]")
    invoice_bill_no = fields.Char(string='Invoice Bill Number', required=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    invoice_date = fields.Date(string='Invoice Bill Date', required=True)
    vendor = fields.Many2one('res.partner', string='Vendor', required=True,  domain="[('supplier', '=', True)]")
    vendor_supply_state = fields.Many2one('res.country.state', string='Vendor Supply State', required=True)
    gst_in = fields.Char(string='GSTIN')
    bill_due_date = fields.Date(string='Bill Due Date', required=True)
    service_category = fields.Many2one('product.category', string='Service Category', required=True)
    month = fields.Selection(month_list, string='Month',required=True)
    generator_name_id = fields.Many2one('generator.company.details', string='Generator', required=True)
    service_item = fields.One2many('service.item', 'service_id')
    service_details = fields.One2many('service.details.item', 'service_id')
    bill_amount = fields.Float(string='Bill Amount', store=True)
    discount_amount = fields.Float(string='Discount Amount', store=True)
    bill_amount_after_discount = fields.Float(string='Bill Amount After Discount', store=True)
    igst_amount = fields.Float(string='IGST Amount', store=True)
    cgst_amount = fields.Float(string='CGST Amount', store=True)
    sgst_amount = fields.Float(string='SGST Amount', store=True)
    total_bill_amount = fields.Float(string='Total Bill Amount', store=True)
    tds = fields.Float(string='TDS', store=True)
    net_due_amount = fields.Float(string='Net Due Amount', store=True)
    igst_pay = fields.Float(string='IGST Pay', store=True)
    cgst_pay = fields.Float(string='CGST Pay', store=True)
    sgst_pay = fields.Float(string='SGST Pay', store=True)
    invoice_raised = fields.Many2one('res.users', string='Invoice Raised By', default=lambda self: self.env.user,track_visibility="onchange")
    is_service = fields.Boolean()

    @api.onchange('cgst_amount')
    def onchange_cgst_amount(self):
        if self.cgst_amount:
            self.sgst_amount = self.cgst_amount

    @api.onchange('sgst_amount')
    def onchange_sgst_amount(self):
        if self.sgst_amount:
            self.cgst_amount = self.sgst_amount

    @api.onchange('bill_amount','discount_amount','igst_amount','cgst_amount','sgst_amount')
    def onchange_bill_amount(self):
        if self.bill_amount or self.discount_amount or self.igst_amount or self.sgst_amount or self.cgst_amount:
            self.bill_amount_after_discount = self.bill_amount - self.discount_amount
            self.total_bill_amount = self.bill_amount - self.discount_amount + self.cgst_amount + self.sgst_amount + self.igst_amount

    @api.onchange('vendor')
    def onchange_vendor(self):
        if self.vendor:
            self.vendor_supply_state = self.vendor.state_id.id or False

    @api.onchange('service_item','service_details')
    def onchange_service_item(self):
        if self.service_item or self.service_details:
            amount =0.0
            discount = 0.0
            cgst_amount = 0.0
            sgst_amount = 0.0
            igst_amount = 0.0
            for line in self.service_item:
                amount += line.amount
                discount += line.discount_amount
                if line.hs_rates.tax_group_id.name == 'SGST' or line.hs_rates.tax_group_id.name == 'CGST':          
                    cgst_amount += line.amount * (line.hs_rates.amount / 100)
                    sgst_amount += line.amount * (line.hs_rates.amount / 100)
                elif line.hs_rates.tax_group_id.name == 'IGST':          
                    igst_amount += line.amount * (line.hs_rates.amount / 100)
            for det in self.service_details:
                amount += det.amount
                discount += det.discount_amount
                if det.sas_rates.tax_group_id.name == 'SGST' or det.sas_rates.tax_group_id.name == 'CGST':          
                    cgst_amount += det.amount * (det.sas_rates.amount / 100)
                    sgst_amount += det.amount * (det.sas_rates.amount / 100)
                elif det.sas_rates.tax_group_id.name == 'IGST':          
                    igst_amount += det.amount * (det.sas_rates.amount / 100)
            self.bill_amount = amount
            self.discount_amount = discount
            self.igst_amount = igst_amount
            self.cgst_amount = cgst_amount
            self.sgst_amount = sgst_amount
        else:
            self.bill_amount = 0.0
            self.discount_amount = 0.0
            self.igst_amount = 0.0
            self.cgst_amount = 0.0
            self.sgst_amount = 0.0
                   
class ServiceItem(models.Model):
    _name = 'service.item'

    service_id = fields.Many2one('service.details')
    item = fields.Many2one('product.product', string='Item', required=True)
    hs_code = fields.Char(string='HSN Code', required=True)
    hs_rates = fields.Many2one('account.tax', string='HSN Rates', required=True)
    sub_ledger = fields.Many2one('account.account',string='Subledger', required=True)
    price = fields.Float(string='Price', required=True)
    qty = fields.Float(string='Quantity', required=True,default=1.0)
    discount_type = fields.Selection([('amt', 'Amt'), ('%', '%')], string='Discount Type',default="amt")
    amount = fields.Float(string='Amount', required=True)
    discount_amount = fields.Float(string='Discount Amount/%', store=True)

    @api.onchange('item')
    def onchange_item(self):
        if self.item:
            self.hs_code = self.item.l10n_in_hsn_code or ''
            self.price = self.item.standard_price or 0.0
        else:
            self.hs_code = ''
            self.price = 0.0
        if self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code == 'AP':
            local_group = self.env['account.tax.group'].search(['|',('name','=','SGST'),('name','=','CGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'hs_rates': [('id', 'in', taxes.ids)]}}
        elif self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code != 'AP':
            local_group = self.env['account.tax.group'].search([('name','=','IGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'hs_rates': [('id', 'in', taxes.ids)]}}

    @api.onchange('qty')
    def onchange_qty(self):
        if self.qty:
            self.amount = self.qty * self.price - self.discount_amount   
            
class ServiceDetails(models.Model):
    _name = 'service.details.item'

    service_id = fields.Many2one('service.details')
    service = fields.Many2one('product.product', string='Service', required=True)
    sub_ledger = fields.Many2one('account.account',string='Subledger', required=True)
    sas_code = fields.Char(string='SAS Code', required=True)
    sas_rates = fields.Many2one('account.tax', string='SAS Rates', required=True)
    amount = fields.Float(string='Amount', required=True)
    discount_type = fields.Selection([('amt', 'Amt'), ('%', '%')], string='Discount Type',default="amt")
    discount_amount = fields.Float(string='Discount Amount/%', store=True)

    @api.onchange('service')
    def onchange_service(self):
        if self.service:
            self.sas_code = self.service.l10n_in_hsn_code or ''
        if self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code == 'AP':
            local_group = self.env['account.tax.group'].search(['|',('name','=','SGST'),('name','=','CGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'sas_rates': [('id', 'in', taxes.ids)]}}
        elif self.service_id.vendor_supply_state and self.service_id.vendor_supply_state.code != 'AP':
            local_group = self.env['account.tax.group'].search([('name','=','IGST')])
            taxes = self.env['account.tax'].search([('tax_group_id','in',local_group.ids)])
            return {'domain': {'sas_rates': [('id', 'in', taxes.ids)]}}
