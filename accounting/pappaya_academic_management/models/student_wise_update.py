from odoo import fields, models, api


class StudentUpdate(models.Model):
    _name = 'student.update'
    _rec_name = 'admission_number'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    admission_number = fields.Char(string="Admission No.")
    branch = fields.Many2one("branch.branch",string="Branch")
    group = fields.Many2one("pappaya.group",string="Group")
    course = fields.Many2one("course.course", string="Course")
    batch = fields.Many2one("batch.batch", string="Batch")
    section = fields.Many2one("section.line", string="Section")
    filter = fields.Many2one("filter.filter", string="Filter")
    student_update_line = fields.One2many("student.update.line", "student_id")


class StudentUpdateLine(models.Model):
    _name = 'student.update.line'
    _rec_name = 'name'

    name = fields.Char(string="Name")
    admission_no = fields.Char(string="Admission No")
    student_id = fields.Many2one("student.update")


class Filter(models.Model):
    _name = 'filter.filter'
    _rec_name = 'name'

    name = fields.Char(string="Filter")













