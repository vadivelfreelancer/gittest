from odoo import fields,models,api


class ExamCourse(models.Model):
    _name = 'exam.course'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    exam_type = fields.Many2one('exam.type', string="Exam Type")
    exam_course_type = fields.One2many('exam.course.line','exam_course_id')


class ExamType(models.Model):
    _name = 'exam.type'
    _rec_name = 'name'

    name = fields.Char(string='Exam Name')


class ExamCourseLine(models.Model):
    _name = 'exam.course.line'
    _rec_name = 'name'

    name = fields.Char(string="Exam Course")
    exam_type = fields.Many2one('exam.type', string="Exam Type")
    description = fields.Text(string="Description")
    exam_course_id = fields.Many2one("exam.course")
