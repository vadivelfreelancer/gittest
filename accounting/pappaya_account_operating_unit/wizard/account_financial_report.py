# © 2016-17 Eficent Business and IT Consulting Services S.L.
# © 2016 Serpent Consulting Services Pvt. Ltd.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models,api


class AccountingReport(models.TransientModel):
    _inherit = "accounting.report"

    report_type = fields.Selection([('entity','Entity wise'),('branch','Branch wise')], 'Report type', default='entity')
    operating_unit_ids = fields.Many2many('operating.unit',
                                          string='Entities/Branches',
                                          required=False)
    
    @api.onchange('report_type')
    def onchange_report_type(self):
        self.operating_unit_ids=False;domain = {};domain['operating_unit_ids'] = [('id','in',[])]
        domain['operating_unit_ids'] = [('id','in',self.env['operating.unit'].sudo().search([('type','=',self.report_type)]).ids)]
        return {'domain':domain}
    

    def _build_contexts(self, data):
        result = super(AccountingReport, self)._build_contexts(data)
        data2 = {}
        data2['form'] = self.read(['operating_unit_ids'])[0]
        result['operating_unit_ids'] = 'operating_unit_ids' in data2['form']\
                                       and data2['form']['operating_unit_ids']\
                                       or False
        return result

    def _build_comparison_context(self, data):
        result = super(AccountingReport, self)._build_comparison_context(data)
        data['form'] = self.read(['operating_unit_ids'])[0]
        result['operating_unit_ids'] = 'operating_unit_ids' in data['form'] \
                                       and data['form']['operating_unit_ids'] \
                                       or False
        return result

    def _print_report(self, data):
        operating_units = ', '.join([ou.name for ou in
                                     self.operating_unit_ids])
        data['form'].update({'operating_units': operating_units})
        return super(AccountingReport, self)._print_report(data)
    
class AccountPrintJournal(models.TransientModel):
    _inherit='account.print.journal'
    
    report_type = fields.Selection([('entity','Entity wise'),('branch','Branch wise')], 'Report type', default='entity')
    operating_unit_ids = fields.Many2many('operating.unit', string='Entities/Branches')
    
    @api.onchange('report_type')
    def onchange_report_type(self):
        self.operating_unit_ids=False;domain = {};domain['operating_unit_ids'] = [('id','in',[])]
        domain['operating_unit_ids'] = [('id','in',self.env['operating.unit'].sudo().search([('type','=',self.report_type)]).ids)]
        return {'domain':domain}    
    
class AccountPartnerLedger(models.TransientModel):
    _inherit = "account.report.partner.ledger"
    
    report_type = fields.Selection([('entity','Entity wise'),('branch','Branch wise')], 'Report type', default='entity')
    operating_unit_ids = fields.Many2many('operating.unit', string='Entities/Branches')
    
    @api.onchange('report_type')
    def onchange_report_type(self):
        self.operating_unit_ids=False;domain = {};domain['operating_unit_ids'] = [('id','in',[])]
        domain['operating_unit_ids'] = [('id','in',self.env['operating.unit'].sudo().search([('type','=',self.report_type)]).ids)]
        return {'domain':domain}
    
    def _build_contexts(self, data):
        result = super(AccountPartnerLedger, self)._build_contexts(data)
        data2 = {}
        data2['form'] = self.read(['operating_unit_ids'])[0]
        result['operating_unit_ids'] = 'operating_unit_ids' \
                                       in data2['form'] and \
                                       data2['form']['operating_unit_ids'] \
                                       or False
        return result

    def _print_report(self, data):
        operating_units = ', '.join([ou.name for ou in
                                     self.operating_unit_ids])
        data['form'].update({'operating_units': operating_units})
        return super(AccountPartnerLedger, self)._print_report(data)    
    
class AccountReportGeneralLedger(models.TransientModel):
    _inherit = "account.report.general.ledger"    

    report_type = fields.Selection([('entity','Entity wise'),('branch','Branch wise')], 'Report type', default='entity')
    operating_unit_ids = fields.Many2many('operating.unit', string='Entities/Branches')
    
    @api.onchange('report_type')
    def onchange_report_type(self):
        self.operating_unit_ids=False;domain = {};domain['operating_unit_ids'] = [('id','in',[])]
        domain['operating_unit_ids'] = [('id','in',self.env['operating.unit'].sudo().search([('type','=',self.report_type)]).ids)]
        return {'domain':domain} 
    
    def _build_contexts(self, data):
        result = super(AccountReportGeneralLedger, self)._build_contexts(data)
        data2 = {}
        data2['form'] = self.read(['operating_unit_ids'])[0]
        result['operating_unit_ids'] = 'operating_unit_ids' \
                                       in data2['form'] and \
                                       data2['form']['operating_unit_ids'] \
                                       or False
        return result

    def _print_report(self, data):
        operating_units = ', '.join([ou.name for ou in
                                     self.operating_unit_ids])
        data['form'].update({'operating_units': operating_units})
        return super(AccountReportGeneralLedger, self)._print_report(data) 
    

class AccountAgedTrialBalance(models.TransientModel):
    _inherit = 'account.aged.trial.balance'
    
    report_type = fields.Selection([('entity','Entity wise'),('branch','Branch wise')], 'Report type', default='entity')
    operating_unit_ids = fields.Many2many('operating.unit', string='Entities/Branches')
    
    @api.onchange('report_type')
    def onchange_report_type(self):
        self.operating_unit_ids=False;domain = {};domain['operating_unit_ids'] = [('id','in',[])]
        domain['operating_unit_ids'] = [('id','in',self.env['operating.unit'].sudo().search([('type','=',self.report_type)]).ids)]
        return {'domain':domain}

    def _build_contexts(self, data):
        result = super(AccountAgedTrialBalance, self)._build_contexts(data)
        data2 = {}
        data2['form'] = self.read(['operating_unit_ids'])[0]
        result['operating_unit_ids'] = 'operating_unit_ids' \
                                       in data2['form'] and \
                                       data2['form']['operating_unit_ids'] \
                                       or False
        return result

    def _print_report(self, data):
        operating_units = ', '.join([ou.name for ou in
                                     self.operating_unit_ids])
        data['form'].update({'operating_units': operating_units})
        return super(AccountAgedTrialBalance, self)._print_report(data) 






