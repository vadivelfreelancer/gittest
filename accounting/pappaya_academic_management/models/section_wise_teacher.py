from odoo import fields, models, api


class SectionClassTeacher(models.Model):
    _name = 'section.class.teacher'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    exam_branch = fields.Many2one('exam.branch', string='Exam Branch')
    section_class_teacher_line = fields.One2many('section.class.teacher.line', 'section_class_teacher_id')


class SectionClassTeacherLine(models.Model):
    _name = 'section.class.teacher.line'

    exam_branch_name = fields.Many2one("exam.branch", string="Exam Branch Name")
    course = fields.Many2one("course.course", string="Course")
    group_name = fields.Many2one("group.group", string="Group Name")
    batch = fields.Many2one("batch.batch", string="Batch")
    section = fields.Many2one("section.line", string="Section")
    strn = fields.Many2one("strn.strn", string="Section")
    section_class_teacher_id = fields.Many2one('section.class.teacher')
    teacher = fields.Many2one("employee.employee", string="Teachers Map")






