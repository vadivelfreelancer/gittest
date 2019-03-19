from odoo import fields,models,api


class ExamTypeTypeView(models.TransientModel):
    _name = 'exam.type.type.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    exam_type_lines = fields.Many2many('exam.type.line')

    @api.model
    def default_get(self, fields):
        res = super(ExamTypeTypeView, self).default_get(fields)
        exam_course = self.env['exam.type.line'].search([])
        res['exam_type_lines'] = exam_course.ids
        return res