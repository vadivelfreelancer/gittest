from odoo import fields, models


class PicCombination(models.Model):
    _name = 'pic.combination'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    select_all = fields.Boolean("Check All/ Uncheck All")
    division = fields.Many2one('division.line', string='Division')
    pgm_in_charge = fields.Many2one('program.incharge.line', string='Program In Charge')
    course_exam = fields.Many2one('course.exam.line', string='Course Exam')
    type = fields.Selection(string="", selection=[('exam_branch', 'Exam Branches'), ('combination', 'Combinations'),],
                            default='exam_branch')
    combinations = fields.Many2many('combination.line')
    branches = fields.Many2many('branch.branch')