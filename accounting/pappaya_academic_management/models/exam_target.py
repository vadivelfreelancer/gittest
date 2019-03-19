from odoo import fields, models, api


class ExamTarget(models.Model):
    _name = 'exam.target'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    exam_target_type = fields.One2many('exam.target.line','exam_target_id')


class ExamCourseLine(models.Model):
    _name = 'exam.target.line'
    _rec_name = 'name'

    name = fields.Char(string="Exam Target")
    status = fields.Selection(string="Status", selection=[('active', 'Active'), ('inactive', 'Inactive'), ])
    exam_target_id = fields.Many2one("exam.target")
