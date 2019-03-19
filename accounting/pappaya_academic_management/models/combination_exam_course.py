from odoo import fields, models, api


class CombinationExamCourse(models.Model):
    _name = 'combination.exam.course'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])

    exam_course = fields.Many2one('exam.course.line', 'Course Exam')
    mapping = fields.Selection(string="Mapping", selection=[('all', 'All'), ('mapping', 'Mapping'),
                                                            ('unmapping', 'Un Mapping'), ], default='all')

    combination_keys = fields.Many2many('combination.line')
    selected_combinations = fields.Many2many('combination.line')

