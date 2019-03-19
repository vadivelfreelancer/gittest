# © 2016-17 Eficent Business and IT Consulting Services S.L.
# © 2016 Serpent Consulting Services Pvt. Ltd.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models,api


class AccountCommonReport(models.TransientModel):
    _inherit = "account.common.report"

    report_type = fields.Selection([('entity','Entity wise'),('branch','Branch wise')])
    operating_unit_ids = fields.Many2many('operating.unit',
                                          string='Entities/Branches',
                                          required=False)
    
    @api.onchange('report_type')
    def onchange_report_type(self):
        self.operating_unit_ids=False;domain = {};domain['operating_unit_ids'] = [('id','in',[])]
        domain['operating_unit_ids'] = [('id','in',self.env['operating.unit'].sudo().search([('type','=',self.report_type)]).ids)]
        return {'domain':domain}
        
    @api.onchange('operating_unit_ids')
    def _onchange_operating_unit_ids(self):
        op_unit_obj = self.env['operating.unit']
        if self.operating_unit_ids:
            for operating_unit in self.operating_unit_ids:
                if operating_unit.child_ids:
                    self.operating_unit_ids = self.operating_unit_ids+operating_unit.child_ids
                else:
                    self.operating_unit_ids = self.operating_unit_ids

    def _build_contexts(self, data):
        result = super(AccountCommonReport, self)._build_contexts(data)
        data2 = {}
        data2['form'] = self.read(['operating_unit_ids'])[0]
        result['operating_unit_ids'] = \
            'operating_unit_ids' in data2['form'] \
            and data2['form']['operating_unit_ids'] or False
        return result
