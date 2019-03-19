# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.tools import float_is_zero, float_compare, pycompat
from odoo.exceptions import Warning
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
import odoo
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re

# TYPE2REFUND = {
#     'out_invoice': 'out_refund',        # Customer Invoice
#     'in_invoice': 'in_refund',          # Vendor Bill
#     'out_refund': 'out_invoice',        # Customer Credit Note
#     'in_refund': 'in_invoice',          # Vendor Credit Note
# }


class ResPartner(models.Model):
    _inherit = "res.partner"

    admission_academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    status = fields.Selection([('new','New'),('soa','SOA'),('reservation','Reservation'),('admission','Admission')], default='new', string='Status')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    # academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    admission_id = fields.Many2one('pappaya.admission', string='Admission', ondelete='cascade')
#     state = fields.Selection([('draft', 'Draft'),('open', 'Open'),('paid', 'Paid'),('cancel', 'Cancelled'),], string='Status', index=True, readonly=True, default='draft', copy=False)
#
#     @api.multi
#     def action_invoice_cancel(self):
#         if self.admission_id:
#             self.admission_id.write({'cancel':1})
#         return super(AccountInvoice, self).action_invoice_cancel()
#
#     @api.model
#     def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
#         """ Prepare the dict of values to create the new credit note from the invoice.
#             This method may be overridden to implement custom
#             credit note generation (making sure to call super() to establish
#             a clean extension chain).
#
#             :param record invoice: invoice as credit note
#             :param string date_invoice: credit note creation date from the wizard
#             :param integer date: force date from the wizard
#             :param string description: description of the credit note from the wizard
#             :param integer journal_id: account.journal from the wizard
#             :return: dict of value to create() the credit note
#         """
#         values = {}
#         for field in self._get_refund_copy_fields():
#             if invoice._fields[field].type == 'many2one':
#                 values[field] = invoice[field].id
#             else:
#                 values[field] = invoice[field] or False
#         ############### For Fees Refund - override exsiting method #############
#         if invoice['type'] == 'out_invoice':
#             if len(self.refund_invoice_ids) > 0:
#                 raise ValidationError('Fees Already Refunded')
#             fees_head =[]
#             for i in self.invoice_line_ids.search([('invoice_id', '=', self.id), ('line_status', '=', 'paid')],
#                                                   order='pay_sequence desc'):
#
#                 head = self.env['pappaya.fees.head'].search([('product_id', '=', i.product_id.id),
#                                                                   ('is_refundable_fee','=',1)])
#                 if head:
#                     fees_head.append(head.product_id.id)
#
#             line_ids = self.invoice_line_ids.search([('invoice_id','=',self.id),('line_status','=','paid'),
#                                                      ('product_id','in',fees_head)],
#                                               order='pay_sequence desc')
#             if len(line_ids.ids) <= 0:
#                 raise ValidationError('No Refund Fees !!!')
#
#             values['invoice_line_ids'] = self._refund_cleanup_lines(line_ids)
#         else:
#             ############### End For Fees Refund - override exsiting method #############
#             values['invoice_line_ids'] = self._refund_cleanup_lines(invoice.invoice_line_ids)
#
#         tax_lines = invoice.tax_line_ids
#         values['tax_line_ids'] = self._refund_cleanup_lines(tax_lines)
#
#         if journal_id:
#             journal = self.env['account.journal'].browse(journal_id)
#         elif invoice['type'] == 'in_invoice':
#             journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
#         else:
#             journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
#         values['journal_id'] = journal.id
#
#         values['type'] = TYPE2REFUND[invoice['type']]
#         values['date_invoice'] = date_invoice or fields.Date.context_today(invoice)
#         values['state'] = 'draft'
#         values['number'] = False
#         values['origin'] = invoice.number
#         values['payment_term_id'] = False
#         values['refund_invoice_id'] = invoice.id
#         if date:
#             values['date'] = date
#         if description:
#             values['name'] = description
#             values['refund_reason'] = description
#         self.admission_id.is_fees_refunded = True
#         return values
#
#     @api.multi
#     def assign_outstanding_credit(self, credit_aml_id):
#         self.ensure_one()
#         credit_aml = self.env['account.move.line'].browse(credit_aml_id)
#         if not credit_aml.currency_id and self.currency_id != self.company_id.currency_id:
#             credit_aml.with_context(allow_amount_currency=True, check_move_validity=False).write({
#                 'amount_currency': self.company_id.currency_id.with_context(date=credit_aml.date).compute(
#                     credit_aml.balance, self.currency_id),
#                 'currency_id': self.currency_id.id})
#         if credit_aml.payment_id:
#             ###################################
#             mov_amount = 0.0
#             for c in credit_aml.payment_id.invoice_ids:
#                 for i in c.payment_ids:
#                     mov_amount+=(i.amount-c.amount_total)
#             bal_amount = 0.0
#             # for inv in r.invoice_ids:
#             for lin in self.invoice_line_ids:
#                 if bal_amount > 0:
#                     mov_amount = bal_amount
#                 if lin.line_status == 'pending':
#                     if lin.pending_amount > mov_amount:
#                         paid_amount = lin.paid_amount + mov_amount
#                         pending_amount = lin.pending_amount - mov_amount
#                         adjusted_amount = lin.adjusted_amount + mov_amount
#                         line_status = 'pending'
#                         lin.write(
#                             {'line_status': line_status, 'adjusted_amount':adjusted_amount,#'paid_amount': paid_amount,
#                              'pending_amount': pending_amount})
#                         credit_aml.payment_id.write({'invoice_ids': [(4, self.id, None)]})
#                         return self.register_payment(credit_aml)
#                         # return super(AccountPayment, self).post()
#                     elif lin.pending_amount <= mov_amount:
#                         paid_amount = lin.paid_amount + lin.pending_amount
#                         adjusted_amount = lin.adjusted_amount + lin.pending_amount
#                         pending_amount = 0.0
#                         bal_amount = mov_amount - lin.pending_amount
#                         line_status = 'paid'
#                         lin.write(
#                             {'line_status': line_status,'adjusted_amount':adjusted_amount,#'paid_amount': paid_amount,
#                              'pending_amount': pending_amount})
#             ###################################
#             credit_aml.payment_id.write({'invoice_ids': [(4, self.id, None)]})
#         return self.register_payment(credit_aml)

#
# class Accountinvline(models.Model):
#     _inherit = "account.invoice.line"
#
#     pay_sequence = fields.Integer('Pay Sequence')
#     actual_amount = fields.Float('Actual Amount')
#     adjusted_amount = fields.Float('Adjusted Amount')
#     paid_amount = fields.Float('Paid Amount')
#     pending_amount = fields.Float('Pending Amount')
#     line_status = fields.Selection([('pending','Pending'),('paid','Paid'),('refund','Refund')], 'Status', default='pending')
#     is_refunded = fields.Boolean('Is Refunded')
#     concession_amount = fields.Float('Concession Amount')

#
# class AccountPayment(models.Model):
#     _inherit = 'account.payment'
#
#     company_id = fields.Many2one(string='Branch',store=True)
#
#     @api.multi
#     def post(self):
#         for r in self:
#             bal_amount = 0.0
#             mov_amount = r.amount
#             for inv in r.invoice_ids:
#                 for lin in inv.invoice_line_ids:
#                     if bal_amount > 0:
#                         mov_amount = bal_amount
#                     if lin.line_status == 'pending':
#                         if lin.pending_amount > mov_amount:
#                             paid_amount = lin.paid_amount + mov_amount
#                             pending_amount = lin.pending_amount - mov_amount
#                             line_status = 'pending'
#                             lin.write(
#                                 {'line_status': line_status, 'paid_amount': paid_amount,
#                                  'pending_amount': pending_amount})
#                             return super(AccountPayment, self).post()
#                         elif lin.pending_amount <= mov_amount:
#                             paid_amount = lin.paid_amount + lin.pending_amount
#                             pending_amount = 0.0
#                             bal_amount = mov_amount - lin.pending_amount
#                             line_status = 'paid'
#                             lin.write(
#                                 {'line_status': line_status, 'paid_amount': paid_amount,
#                                  'pending_amount': pending_amount})
#             #################### END END #########################################
#         return super(AccountPayment, self).post()
