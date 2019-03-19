from odoo import api, fields, models


class ExamTypeType(models.Model):
    _name = 'exam.type.type'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    combination_line_line = fields.One2many('exam.type.line', 'exam_type_id')


class CombinationLine(models.Model):
    _name = 'exam.type.line'
    _rec_name = 'name'

    name = fields.Char()
    description = fields.Text(string="Description")
    exam_type = fields.Many2one('exam.type', 'Exam Type')
    exam_type_id = fields.Many2one("exam.type.type", string="")
