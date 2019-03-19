from odoo import api, fields, models


class PreviousView(models.TransientModel):
    _name = 'combination.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    course = fields.Many2one('course.course', string='Course')
    combination_lines = fields.Many2many('combination.line')

    @api.model
    def default_get(self, fields):
        res = super(PreviousView, self).default_get(fields)
        previous = self.env['combination.line'].search([])
        res['combination_lines'] = previous.ids
        return res
