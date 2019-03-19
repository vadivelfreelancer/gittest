from odoo import api, fields, models


class GetBranches(models.TransientModel):
    _name = 'get.branches.wizard'

    sub_ledger_id = fields.Many2one("account.account", string="Sub Ledger", readonly="1")
    branch_ids = fields.One2many('branch.list', 'branch_id', string="Branches")

    @api.model
    def default_get(self, fields):
        res = super(GetBranches, self).default_get(fields)
        result = []
        if self.env.context.get('active_id'):
            m_bank_payment_id = self.env.context.get('active_id')
            voucher = self.env['pappaya.journal.voucher'].browse(m_bank_payment_id)
            if voucher:
                branch_ids = self.env['branch.ledger'].search([('sub_ledger', '=', voucher.branch_ledger_id.id)])
                if branch_ids:
                    for line in branch_ids.branch_ledger:
                        branch_id = self.env['page.ledger'].browse(line.id)
                        print("------------>>>>>>>>>>>>", branch_id.branch)
                        result.append((0, 0, {'branch': branch_id.branch.id, 'check_bool': False }))
                    res['branch_ids'] = result
                    res['sub_ledger_id'] = voucher.branch_ledger_id.id
                else:
                    res['sub_ledger_id'] = voucher.branch_ledger_id.id
        return res

class BranchList(models.TransientModel):
    _name = 'branch.list'

    branch_id = fields.Many2one('get.branches.wizard', string="Get Branches")
    branch = fields.Many2one('operating.unit', string="Branch")
    check_bool = fields.Boolean(string="Select")
