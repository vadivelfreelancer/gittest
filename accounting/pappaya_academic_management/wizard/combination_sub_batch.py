from odoo import api, fields, models


class CombinationSubBatch(models.TransientModel):
    _name = 'combination.sub.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    combination = fields.Many2one('combination.combination', string='')
    combination_subbatch_lines = fields.Many2many('combination.sub.line')

    @api.model
    def default_get(self, fields):
        res = super(CombinationSubBatch, self).default_get(fields)
        comb_batch = self.env['combination.sub.line'].search([])
        res['combination_subbatch_lines'] = comb_batch.ids
        return res