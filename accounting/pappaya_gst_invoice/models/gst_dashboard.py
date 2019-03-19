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

import json
from datetime import datetime, timedelta

from babel.dates import format_datetime, format_date

from odoo import models, api, _, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.misc import formatLang

class gst_dashboard(models.Model):
    _name = "gst.dashboard"
    _description = "Gst Dashboard"

    @api.one
    def _kanban_dashboard_graph(self):
        self.kanban_dashboard_graph = json.dumps(self.get_bar_graph_datas(self.invoice_type))

    @api.one
    def _get_count(self):
        not_upload_count = len(self.env['account.invoice'].search([('invoice_type', '=' ,self.invoice_type),('gst_status', '=' ,'not_uploaded')]))
        ready_count = len(self.env['account.invoice'].search([('invoice_type', '=' ,self.invoice_type),('gst_status', '=' ,'ready_to_upload')]))
        uploaded_count = len(self.env['account.invoice'].search([('invoice_type', '=' ,self.invoice_type),('gst_status', '=' ,'uploaded')]))
        filed_count = len(self.env['account.invoice'].search([('invoice_type', '=' ,self.invoice_type),('gst_status', '=' ,'filed')]))
        self.not_upload_count = not_upload_count
        self.ready_count = ready_count
        self.uploaded_count = uploaded_count
        self.filed_count = filed_count

    @api.one
    def _get_amount(self):
        not_upload_amount = self.getTotalAmount('not_uploaded')
        ready_amount = self.getTotalAmount('ready_to_upload')
        uploaded_amount = self.getTotalAmount('uploaded')
        filed_amount = self.getTotalAmount('filed')
        self.not_upload_amount = not_upload_amount
        self.ready_amount = ready_amount
        self.uploaded_amount = uploaded_amount
        self.filed_amount = filed_amount

    def getTotalAmount(self, gst_status):
        inr_total = 0
        invoiceObjs = self.env['account.invoice'].search([('invoice_type', '=' ,self.invoice_type),('gst_status', '=' ,gst_status)])
        for invoiceObj in invoiceObjs:
            inr_total += invoiceObj.inr_total
        return inr_total
    
    color = fields.Integer(string='Color Index')
    not_upload_count = fields.Integer(string='Not Uploaded Count', compute='_get_count')
    ready_count = fields.Integer(string='Ready to Upload Count', compute='_get_count')
    uploaded_count = fields.Integer(string='Uploaded Count', compute='_get_count')
    filed_count = fields.Integer(string='Filed Count', compute='_get_count')
    not_upload_amount = fields.Integer(string='Not Uploaded Amount', compute='_get_amount')
    ready_amount = fields.Integer(string='Ready to Upload Amount', compute='_get_amount')
    uploaded_amount = fields.Integer(string='Uploaded Amount', compute='_get_amount')
    filed_amount = fields.Integer(string='Filed Amount', compute='_get_amount')
    name = fields.Char(string="Name",size=100)
    kanban_dashboard_graph = fields.Text(compute='_kanban_dashboard_graph')
    invoice_type = fields.Selection([
                                ('b2b', 'B2B'),
                                ('b2bur', 'B2BUR'),
                                ('b2cl', 'B2CL'),
                                ('b2cs', 'B2CS'),
                                ('import', 'Import'),
                                ('export', 'Export')
                            ])

    @api.multi
    def open_action(self):
        self.ensure_one()
        itemType = self.invoice_type
        vals = [('invoice_type', '=' ,itemType)]
        res = self.get_action_records(vals)
        return res

    @api.multi
    def get_attachments(self):
        self.ensure_one()
        name = "{}_".format(self.invoice_type)
        if self.invoice_type == 'import':
            name = "imp_"
        itemIds = self.env['ir.attachment'].search([('name', 'ilike', name), ('res_model','=','gstr1.tool')])
        itemIds = itemIds.ids
        return {
                'name': ('Attachment'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'ir.attachment',
                'view_id': False,
                'domain': [('id', 'in', itemIds)],
                'target': 'current',
            }

    @api.multi
    def get_gst_invoice(self):
        self.ensure_one()
        ctx = self._context.copy()
        name = "{}_".format(self.invoice_type)
        itemObjs = self.env['ir.attachment'].search([('name', 'ilike', name), ('res_model','=','gstr1.tool')])
        itemIds = []
        for itemObj in itemObjs:
            itemIds.append(itemObj.res_id)
        if ctx.get('status'):
            itemIds = self.env['gstr1.tool'].search([('status', '=', ctx.get('status')), ('id','in', itemIds)]).ids
        return {
                'name': ('GST Invoices'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'gstr1.tool',
                'view_id': False,
                'domain': [('id', 'in', itemIds)],
                'target': 'current',
            }

    @api.multi
    def action_create_new(self):
        ctx = self._context.copy()
        model = 'gstr1.tool'
        view_id = self.env.ref('gst_invoice.gstr1_tool_form').id
        name = "GST Invoice"
        if ctx.get('obj') == 'Invoice':
            model = 'account.invoice'
            ctx.update({'default_type': 'out_invoice', 'type': 'out_invoice', 'invoice_type':self.invoice_type})
            view_id = self.env.ref('account.invoice_form').id
            name = "Create Invoice"
        return {
            'name': _(name),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': model,
            'view_id': view_id,
            'context': ctx,
        }

    @api.multi
    def get_gst_action(self):
        self.ensure_one()
        ctx = self._context.copy()
        itemType = self.invoice_type
        vals = [('invoice_type', '=' ,itemType)]
        if ctx.get('gst_status'):
            vals.append(('gst_status', '=' ,ctx.get('gst_status')))
        res = self.get_action_records(vals)
        return res

    @api.multi
    def get_action_records(self, vals=[]):
        self.ensure_one()
        recordIds = self.env['account.invoice'].search(vals).ids
        return {
                'name': ('Records'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'view_id': False,
                'domain': [('id', 'in', recordIds)],
                'target': 'current',
            }

    @api.multi
    def get_bar_graph_datas(self, invoice_type):
        self.ensure_one()
        # itemType = self.item_name
        # if itemType in ['order', 'partner']:
        #     fecthDate = 'create_date'
        # else:
        #     fecthDate = 'write_date'
        moduleTable = 'account_invoice'
        fecthDate = 'date_invoice'
        data = []
        today = datetime.strptime(fields.Date.context_today(self), DF)
        data.append({'label': _('Past'), 'value':0.0, 'type': 'past'})
        day_of_week = int(format_datetime(today, 'e', locale=self._context.get('lang', 'en_US')))
        first_day_of_week = today + timedelta(days=-day_of_week+1)
        for i in range(-1,2):
            if i==0:
                label = _('This Week')
            elif i==1:
                label = _('Future')
            else:
                start_week = first_day_of_week + timedelta(days=i*7)
                end_week = start_week + timedelta(days=6)
                if start_week.month == end_week.month:
                    label = str(start_week.day) + '-' +str(end_week.day)+ ' ' + format_date(end_week, 'MMM', locale=self._context.get('lang', 'en_US'))
                else:
                    label = format_date(start_week, 'd MMM', locale=self._context.get('lang', 'en_US'))+'-'+format_date(end_week, 'd MMM', locale=self._context.get('lang', 'en_US'))
            data.append({'label':label,'value':0.0, 'type': 'past' if i<0 else 'future'})

        # Build SQL query to find amount aggregated by week
        select_sql_clause = """SELECT COUNT(*) as total FROM """ + moduleTable + """ where invoice_type = %(invoice_type)s """
        query = ''
        start_date = (first_day_of_week + timedelta(days=-7))
        for i in range(0,4):
            if i == 0:
                query += "("+select_sql_clause+" and " + fecthDate + " < '"+start_date.strftime(DF)+"')"
            elif i == 3:
                query += " UNION ALL ("+select_sql_clause+" and date >= '"+start_date.strftime(DF)+"')"
            else:
                next_date = start_date + timedelta(days=7)
                query += " UNION ALL ("+select_sql_clause+" and " + fecthDate + " >= '"+start_date.strftime(DF)+"' and " + fecthDate + " < '"+next_date.strftime(DF)+"')"
                start_date = next_date

        self.env.cr.execute(query, {'invoice_type':self.invoice_type})
        query_results = self.env.cr.dictfetchall()
        for index in range(0, len(query_results)):
            total = str(query_results[index].get('total'))
            total = total.split('L')
            if int(total[0]) > 0:
                data[index]['value'] = total[0]

        return [{'values': data}]