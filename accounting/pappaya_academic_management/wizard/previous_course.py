from odoo import fields, models, api


class PreviousView(models.TransientModel):
    _name = 'previous.view'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    previous = fields.Many2many('courses.line')

    @api.model
    def default_get(self, fields):
        res = super(PreviousView, self).default_get(fields)
        previous = self.env['courses.line'].search([])
        res['previous'] = previous.ids
        return res
