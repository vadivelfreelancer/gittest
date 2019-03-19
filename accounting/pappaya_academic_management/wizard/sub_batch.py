from odoo import api, fields, models


class PreviousView(models.TransientModel):
    _name = 'sub.batch.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    sub_batch_lines = fields.Many2many('subbatch.line')

    @api.model
    def default_get(self, fields):
        res = super(PreviousView, self).default_get(fields)
        previous = self.env['subbatch.line'].search([])
        res['sub_batch_lines'] = previous.ids
        return res