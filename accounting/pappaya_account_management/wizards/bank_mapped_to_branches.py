from odoo import api, fields, models


class BranchFyLink(models.TransientModel):
    _name = 'bank.subledger.fy.wizard'

    financial_year = fields.Many2one('financial.year', string='Financial Year', required=True)
    bank = fields.Many2one('single.ledger', string='Bank', domain="[('is_bank', '=', 'yes')]", required=True)
    branches = fields.Many2many('operating.unit', string='Branch', required=True)

    @api.onchange('financial_year', 'bank')
    def update_sub_ledgers(self):
        for record in self:
            if record.financial_year and record.bank:
                for item in record.bank.fy_banks:
                    if record.financial_year == item.financial_year:
                        record.branches = item.branches

    @api.model
    def create(self, values):
        if values.get('financial_year') and values.get('bank'):
            fy = self.env['financial.year'].browse(values.get('financial_year'))
            bank = self.env['single.ledger'].browse(values.get('bank'))
            in_branch = False
            for item in bank.fy_banks:
                if item.financial_year == fy:
                    item.branches = values.get('branches')
                    in_branch = True
            if not in_branch:
                bank.fy_banks.create({'financial_year': values.get('financial_year'),
                                      'branches': values.get('branches'),
                                      'bank': bank.id})
        return super(BranchFyLink, self).create(values)
