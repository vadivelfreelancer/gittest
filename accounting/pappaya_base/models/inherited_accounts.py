# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
import odoo
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re

class PappayaJournal(models.Model):
    _inherit = 'account.journal'

    is_cheque = fields.Boolean('Is Cheque')
    is_card = fields.Boolean('Is Card')

    @api.onchange('is_cheque')
    def onchange_cheque(self):
        if self.is_cheque:
            self.is_card = False

    @api.onchange('is_card')
    def onchange_card(self):
        if self.is_card:
            self.is_cheque = False


class PappayaAccountPayment(models.Model):
    _inherit = 'account.payment'

    cheque_dd = fields.Char('Cheque/DD/POS/Ref. No', size=30)
    bank_name = fields.Many2one('res.bank', 'Bank Name')
    remarks = fields.Text('Remarks' ,size=200)

    @api.onchange('cheque_dd')
    def onchange_cheque_dd(self):
        for rec in self:
            if rec.cheque_dd:
                cheque_dd = re.match('^[\d]*$', rec.cheque_dd)
                if not cheque_dd:
                    raise ValidationError(_("Please enter a valid Cheque/DD/POS/Ref.No"))

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            self.currency_id = self.journal_id.currency_id or self.company_id.currency_id
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False
            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'
            ######
            invisible = 1
            if self.journal_id.is_cheque or self.journal_id.is_card:
                invisible = 0
            return {'domain': {
                        'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods.ids)]},
                    }
        return {}


class account_tax(models.Model):
    _inherit = 'account.tax'

    gst_type = fields.Selection([('inter_state', 'Inter State'),('intra_state','Intra State'),('non_gst','Non GST')], 'GST Type')
    tax_on_price = fields.Selection([('inclusive', 'Inclusive'),('exclusive','Exclusive')],"Price type",  default='exclusive')

