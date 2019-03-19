from odoo import api, fields, models


class PreviousCourseBatch(models.TransientModel):
    _name = 'previous.course.previous.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    previous_course_lines = fields.Many2many("previous.course.type.line")

    @api.model
    def default_get(self, fields):
        res = super(PreviousCourseBatch, self).default_get(fields)
        previous_course_batch = self.env['previous.course.type.line'].search([])
        res['previous_course_lines'] = previous_course_batch.ids
        return res