from odoo import api, fields, models


class SubSectionInChargeMap(models.Model):
    _name = 'sub.section.incharge.map'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    exam_branch = fields.Many2one("exam.branch", string="Exam Branch")
    course = fields.Many2one("course.course", string="Course")
    group = fields.Many2one('pappaya.group', string='Group')
    sub_section = fields.Many2one("sub.section.line", string="Subsection")
    employee_no = fields.Char(string="Employee No")
    name = fields.Char(string="Name")


class ExamBranch(models.Model):
    _name = 'exam.branch'
    _rec_name = 'name'

    name = fields.Char(string="Exam Branch")

