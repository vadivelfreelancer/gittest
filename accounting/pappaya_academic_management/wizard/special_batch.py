from odoo import api, fields, models


class PreviousView(models.TransientModel):
    _name = 'special.batch.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    special_batch_lines = fields.Many2many('special.batch.line')

    @api.model
    def default_get(self, fields):
        res = super(PreviousView, self).default_get(fields)
        previous = self.env['special.batch.line'].search([])
        res['special_batch_lines'] = previous.ids
        return res