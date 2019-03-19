from odoo import fields, models, api


class PreviousCourse(models.Model):
    _name = 'previous.course'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    previous_courses = fields.One2many('courses.line', 'previous_course_id')


class CoursesLine(models.Model):
    _name = 'courses.line'

    name = fields.Char(string="Previous Course")
    is_external = fields.Boolean(string="External Exam")
    description = fields.Text(string="Description")
    result_entry = fields.Selection(string="Result Entry",
                                    selection=[('manual', 'Manual'), ('results', 'Results'), ])
    previous_course_id = fields.Many2one('previous.course')