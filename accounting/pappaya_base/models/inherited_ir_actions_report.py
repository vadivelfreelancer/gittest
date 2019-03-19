# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    # Purpose: Report generated directly.
    # Need not to select the report template at the start
    @api.multi
    def get_report_action(self, docids, data=None):
        context = self.env.context
        if docids:
            if isinstance(docids, models.Model):
                active_ids = docids.ids
            elif isinstance(docids, int):
                active_ids = [docids]
            elif isinstance(docids, list):
                active_ids = docids
            context = dict(self.env.context, active_ids=active_ids)
        return {
            'context': context,
            'data': data,
            'type': 'ir.actions.report',
            'report_name': self.report_name,
            'report_type': self.report_type,
            'report_file': self.report_file,
            'name': self.name,
        }
        
        
class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    
    company_id = fields.Many2one('res.company', string='Organization', change_default=True,default=lambda self: self.env['res.company']._company_default_get('ir.attachment'))