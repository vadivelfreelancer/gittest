from odoo import fields, models


class AttendanceLock(models.Model):
    _name = 'attendance.lock'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    select_all = fields.Boolean("Check All Course")
    courses = fields.Many2many('course.course')
