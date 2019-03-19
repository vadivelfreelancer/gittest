from odoo import fields, models, api


class SubjectsView(models.TransientModel):
    _name = 'subjects.view'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    subjects = fields.Many2many('subject.line')

    @api.model
    def default_get(self, fields):
        res = super(SubjectsView, self).default_get(fields)
        subjects = self.env['subject.line'].search([])
        res['subjects'] = subjects.ids
        return res
