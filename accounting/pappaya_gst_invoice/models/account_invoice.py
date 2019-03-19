#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

import odoo
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class GstAccountInvoice(models.Model):
    _inherit = "account.invoice"

    gst_status = fields.Selection([
                                ('not_uploaded', 'Not Uploaded'),
                                ('ready_to_upload', 'Ready to upload'),
                                ('uploaded', 'Uploaded to govt'),
                                ('filed', 'Filed')
                            ],
                            string='GST Status',
                            default="not_uploaded",
                            copy=False,
                            help="status will be consider during gst import, "
            )
    invoice_type = fields.Selection([
                                ('b2b', 'B2B'),
                                ('b2cl', 'B2CL'),
                                ('b2cs', 'B2CS'),
                                ('b2bur', 'B2BUR'),
                                ('import', 'IMPS/IMPG'),
                                ('export', 'Export')
                            ],
                            copy=False,
                            string='Invoice Type'
            )
    export = fields.Selection([
                                ('WPAY', 'WPay'),
                                ('WOPAY', 'WoPay')
                            ],
                            string='Export'
            )
    portcode_id = fields.Many2one('port.code', 'Place of Supply', help="Enter the six digit code of port through which goods were imported")
    inr_total = fields.Float(string='INR Total')
    port_code = fields.Char(
        string='Place of Supply',
        copy=False,
        help='Enter the six digit code of port through which goods were exported. Please refer to the list of port codes available on the GST common portal.')
    shipping_bill_number = fields.Char(
        string='Shipping Bill Number',
        copy=False,
        help='Enter the unique reference number of shipping bill. This information if not available at the timing of submitting the return the same may be left blank and provided later.',size=100)
    shipping_bill_date = fields.Date(
        string='Shipping Bill Date',
        copy=False,
        help="Enter date of shipping bill in DD-MMM-YYYY. E.g. 24-May-2017.")

    # @api.onchange('invoice_line_ids')
    # def _onchange_invoice_line_ids(self):
    #     taxes_grouped = self.get_hsn_taxes_values()
    #     tax_lines = self.tax_line_ids.browse([])
    #     for yo in taxes_grouped.values():
    #         for tax in yo.values():
    #             tax_lines += tax_lines.new(tax)
    #         self.tax_line_ids = tax_lines
    #     print ("222222222222222222222222222222222222222222222222222")
    #     return

    @api.multi
    def get_hsn_taxes_values(self):
        tax_hsn_grouped = {}
        tax_grouped = {}
        for line in self.invoice_line_ids:
            hsn =line.product_id.l10n_in_hsn_code
            hsnVal = hsn
            if not hsnVal:
                hsnVal = 'false'
            if hsnVal not in tax_hsn_grouped:
                tax_hsn_grouped[hsnVal] = {}
            price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.invoice_line_tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
            for tax in taxes:
                val = self._prepare_tax_line_vals(line, tax)
                key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)
                if key not in tax_hsn_grouped[hsnVal]:
                    val['hsn_code'] = hsn
                    tax_hsn_grouped[hsnVal][key] = val
                else:
                    tax_hsn_grouped[hsnVal][key]['amount'] += val['amount']
                    tax_hsn_grouped[hsnVal][key]['base'] += val['base']

        return tax_hsn_grouped


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    hsn_code = fields.Char(string='HSN', copy=False)



### Changes made by T42 Dev
class account_tax(models.Model):
    _inherit = 'account.tax'

    gst_type = fields.Selection([('inter_state', 'Inter State'),('intra_state','Intra State'),('non_gst','Non GST')], 'GST Type')
    po_price_include = fields.Selection([('inclusive', 'Inclusive'),('exclusive','Exclusive')],"Price type",  default='exclusive')


class product_template_inherit(models.Model):
    _inherit = 'product.template'

    @api.constrains('supplier_taxes_id')
    def check_supplier_taxes_gst(self):
        if self.supplier_taxes_id:
            cgst_count = 0
            igst_count = 0
            for i in self.supplier_taxes_id:
                if i.gst_type == 'inter_state':
                    igst_count+=1
                if i.gst_type == 'intra_state':
                    cgst_count+=1

            if cgst_count > 0 or igst_count > 0:
                if cgst_count == 2 and igst_count == 2:
                    return True
                else:
                    raise UserError('Product should have only two GST and two IGST configured')

    @api.constrains('taxes_id')
    def check_customer_taxes_gst(self):
        print ("Customer Taxes id =================================")
        if self.taxes_id:
            cgst_count = 0
            igst_count = 0
            for i in self.taxes_id:
                if i.gst_type == 'inter_state':
                    igst_count += 1
                if i.gst_type == 'intra_state':
                    cgst_count += 1

            if cgst_count > 0 or igst_count > 0:
                if cgst_count == 2 and igst_count == 2:
                    return True
                else:
                    raise UserError('Product should have only two GST and two IGST configured')



class purchase_order_line_inherit(models.Model):
    _inherit = 'purchase.order.line'

    apply_gst_as  = fields.Selection([('inclusive', 'Inclusive'),('exclusive','Exclusive')], 'Applying GST as', default='exclusive')

    @api.onchange('product_id','apply_gst_as')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result

        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.price_unit = self.product_qty = 0.0
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

        product_lang = self.product_id.with_context(
            lang=self.partner_id.lang,
            partner_id=self.partner_id.id,
        )
        self.name = product_lang.display_name
        if product_lang.description_purchase:
            self.name += '\n' + product_lang.description_purchase

        fpos = self.order_id.fiscal_position_id

        inter_ids=[]
        intra_ids=[]

        for t in self.product_id.supplier_taxes_id:
            if t.gst_type == 'inter_state':
                if self.apply_gst_as == t.po_price_include:
                    inter_ids.append(t.id)
            elif t.gst_type == 'intra_state':
                if self.apply_gst_as == t.po_price_include:
                    intra_ids.append(t.id)

        if self.env.uid == SUPERUSER_ID:
            # company_id = self.env.user.company_id.id
            # self.taxes_id = fpos.map_tax(
            #     self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))

            if self.order_id.partner_id.state_id == self.order_id.company_id.state_id:
                self.taxes_id = [(6,0,intra_ids)]
            else:
                self.taxes_id = [(6,0,inter_ids)]


        else:
            # self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)
            if self.order_id.partner_id.state_id == self.order_id.company_id.state_id:
                self.taxes_id = [(6,0,intra_ids)]
            else:
                self.taxes_id = [(6,0,inter_ids)]

        self._suggest_quantity()
        self._onchange_quantity()

        return result

    # @api.depends('product_qty', 'price_unit', 'taxes_id','apply_gst_as')
    # def _compute_amount(self):
    #     for line in self:
    #         tax_per_tot =0.0
    #         for t in line.taxes_id:
    #             tax_per_tot+=t.amount
    #         print (tax_per_tot, "=====================================================================")
    #         taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty,
    #                                           product=line.product_id, partner=line.order_id.partner_id)
    #         print (taxes,"------------------------------------------")
    #         line.update({
    #             'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
    #             'price_total': taxes['total_included'],
    #             'price_subtotal': taxes['total_excluded'],
    #         })


class purchase_order_inherit(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.fiscal_position_id = False
            self.payment_term_id = False
            self.currency_id = False
        else:
            self.fiscal_position_id = self.env['account.fiscal.position'].with_context(
                company_id=self.company_id.id).get_fiscal_position(self.partner_id.id)
            self.payment_term_id = self.partner_id.property_supplier_payment_term_id.id
            self.currency_id = self.partner_id.property_purchase_currency_id.id or self.env.user.company_id.currency_id.id

            inter_ids = []
            intra_ids = []
            for l in self.order_line:
                for t in l.product_id.supplier_taxes_id:
                    if t.gst_type == 'inter_state':
                        if l.apply_gst_as == t.po_price_include:
                            inter_ids.append(t.id)
                    elif t.gst_type == 'intra_state':
                        if l.apply_gst_as == t.po_price_include:
                            intra_ids.append(t.id)
                if self.partner_id.state_id == self.company_id.state_id:
                    l.taxes_id = [(6, 0, intra_ids)]
                else:
                    l.taxes_id = [(6, 0, inter_ids)]

        return {}