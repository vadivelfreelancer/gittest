from odoo import fields, models


class DefineHoliday(models.Model):
    _name = 'define.holiday'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    date = fields.Date(string="Date")
    exam_branch = fields.Many2one("exam.branch", string="Exam branch")
    attendance_type = fields.Many2one("attendance.type.line", string="Attendance Type")
    define_holiday_line = fields.One2many('define.holiday.line', 'holiday_id')


class DefineHolidayLine(models.Model):
    _name = 'define.holiday.line'

    course = fields.Many2one("pappaya.course", string="Course")
    group = fields.Many2one("pappaya.group", string="Group")
    batch = fields.Many2one("pappaya.batch", string="Batch")
    sub_batch = fields.Many2one("subbatch.line", string="Sub Batch")
    section = fields.Many2one("section.line", string="Section")
    working = fields.Selection(string="Working/Holiday", selection=[('working', 'Working'), ('holiday', 'Holiday'), ])
    holiday_id = fields.Many2one('define.holiday')
