from odoo import fields,models,api


class ExamCourseView(models.TransientModel):
    _name = 'exam.course.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    exam_type = fields.Many2one('exam.type', string="Exam Type")
    exam_course_lines = fields.Many2many('exam.course.line')

    @api.model
    def default_get(self, fields):
        res = super(ExamCourseView, self).default_get(fields)
        exam_course = self.env['exam.course.line'].search([])
        res['exam_course_lines'] = exam_course.ids
        return res


