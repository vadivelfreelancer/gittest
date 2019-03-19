from odoo import fields, models, api


class AttendanceRange(models.Model):
    _name = 'attendance.range'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    attendance_range_lines = fields.One2many("attendance.range.line", "attendance_range_id")


class BranchSectionLine(models.Model):
    _name = 'attendance.range.line'

    range_from = fields.Char(string="Range From")
    range_to = fields.Char(string="Range To")
    is_active = fields.Boolean(string="Active/Inactive")
    attendance_range_id = fields.Many2one('attendance.range')






