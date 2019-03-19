from odoo import api, fields, models


class StudentSectionMaster(models.Model):
    _name = 'student.section.map'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])

    exam_branch = fields.Many2one("exam.branch", string="Exam Branch")
    group = fields.Many2one('pappaya.group', 'Group')
    course = fields.Many2one('course.course', string='Course')
    batch = fields.Many2one('batch.batch', 'Batch')
    medium = fields.Many2one("section.medium", string="Medium")
    student_type = fields.Many2one("student.type", string="Student Type")
    gender = state = fields.Selection(string="Gender",
                                      selection=[('all', 'All'), ('male', 'Male'), ('female', 'Female'), ])
    section = fields.Many2one('section.line', string='Section')
    date = fields.Date(string="Date")

    student_section_map_line_ids = fields.One2many("student.section.map.line", "student_section_map_id", string="")


class StudentSectionSingleMode(models.Model):
    _name = 'student.section.map.line'
    _description = "StudentSection(SingleMode)"

    student_section_map_id = fields.Many2one("student.section.map", string="")
    admission_no = fields.Many2one("admission.number", string="Admission Number")
    student_name = fields.Char('Student')
    section = fields.Many2one('section.line', string='Section')
    exam_branch = fields.Many2one("exam.branch", string="Exam Branch")
    branch = fields.Many2one("branch.branch", string="Branch")
    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', 'Group')
    batch = fields.Many2one('batch.batch', 'Batch')
    medium = fields.Many2one("section.medium", string="Medium")
    gender = state = fields.Selection(string="Gender",
                                      selection=[('all', 'All'), ('male', 'Male'), ('female', 'Female'), ])
    student_type = fields.Many2one("student.type", string="Student Type")


class StudentType(models.Model):
    _name = 'student.type'
    _rec_name = 'name'

    name = fields.Char()


class SectionMedium(models.Model):
    _name = 'section.medium'
    _rec_name = 'name'

    name = fields.Char()

