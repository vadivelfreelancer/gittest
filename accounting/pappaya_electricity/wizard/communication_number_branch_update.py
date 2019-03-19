from odoo import models, fields, api


class CommunicationNumberBranchUpdate(models.Model):
    _name = 'branch.update'

    branch_id = fields.Many2one('operating.unit', string='Branch', required=True)
    communication_number = fields.Many2one('communication.details', string='Communication Number', required=True,
                                           domain="[('branch_id', '=', branch_id), ('state', '=', 'approved')]")
    new_branch_id = fields.Many2one('operating.unit', string='New Branch', domain="[('id', '!=', branch_id)]", required=True)
    transfer_date = fields.Date(string='Transfer Date', required=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, track_visibility="onchange")

    @api.model
    def create(self, vals):
        res = super(CommunicationNumberBranchUpdate, self).create(vals)
        res.communication_number.branch_id = res.new_branch_id.id
        res.communication_number.transfer_branch = res.branch_id.id
        res.communication_number.transfer_date = res.transfer_date
        res.communication_number
        return res