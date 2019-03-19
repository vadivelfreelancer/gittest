from odoo import fields,models,api


class ExamNameView(models.TransientModel):
    _name = 'exam.name.view'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one('course.course', string='Course')
    exam_name_line = fields.Many2many('exam.name.line')

    @api.model
    def default_get(self, fields):
        res = super(ExamNameView, self).default_get(fields)
        exam_name = self.env['exam.name.line'].search([])
        res['exam_name_line'] = exam_name.ids
        return res