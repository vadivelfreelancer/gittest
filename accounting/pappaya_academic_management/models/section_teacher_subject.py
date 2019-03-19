from odoo import fields, models, api


class SectionTeacherSubject(models.Model):
    _name = 'section.teacher.subject'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    branch = fields.Many2one("branch.branch", string="Branch")
    course = fields.Many2one("exam.course.line", string="")
    group = fields.Many2one("pappaya.group", string="Group")
    batch = fields.Many2one("batch.batch", string="Batch")
    section = fields.Many2one("section.line", string="Section")
    section_teacher_line = fields.One2many("section.teacher.line", "section_teacher_id")


class SectionTeacherLine(models.Model):
    _name = 'section.teacher.line'

    subject = fields.Many2one("subject.line", string="Subject")
    faculty = fields.Many2one("faculty.faculty", string="Faculty")
    section_teacher_id = fields.Many2one("section.teacher.subject")


class Faculty(models.Model):
    _name = 'faculty.faculty'

    name = fields.Char(string="Faculty Name")


