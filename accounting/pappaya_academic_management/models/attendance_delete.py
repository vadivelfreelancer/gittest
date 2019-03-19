from odoo import fields, models, api


class AttendanceDelete(models.Model):
    _name = 'attendance.delete'
    _rec_name = 'exam_branch'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    exam_branch = fields.Many2one("exam.branch", string="Exam Branch")
    course = fields.Many2one("course.course", string="Course")
    sub_batch = fields.Many2one("subbatch.line", string="Sub Batch")
    section = fields.Many2one("section.line", string="Section")
    attendance_type = fields.Many2one("attendance.type.line", string="Attendance Type")
    date = fields.Date(string="Date")



    










