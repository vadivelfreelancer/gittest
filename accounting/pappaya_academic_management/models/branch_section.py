from odoo import fields, models, api


class BranchSection(models.Model):
    _name = 'branch.section'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    exam_branch = fields.Many2one('exam.branch', string='Select Exam Branch')
    branch_section_lines = fields.One2many("branch.section.line", "branch_section_id", string="")


class BranchSectionLine(models.Model):
    _name = 'branch.section.line'

    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', string='Group')
    batch = fields.Many2one('batch.batch', string='Batch')
    new_sub_batch = fields.Many2one('new.subbatch.line', string='New SubBatch')
    strn = fields.Many2one('strn.strn', string='STRN')
    section = fields.Many2one('section.line', string='Mapped Section')
    sec_strn = fields.Many2one('sec.strn', string='Sec[STRN]')
    new = fields.Many2one('sec.strn', string='New')
    edit = fields.Many2many('sec.strn', string='edit')

    branch_section_id = fields.Many2one('branch.section')


class Strn(models.Model):
    _name = 'strn.strn'
    _rec_name = 'name'

    name = fields.Char(sting='Strn')


class Strn(models.Model):
    _name = 'sec.strn'
    _rec_name = 'name'

    name = fields.Integer(sting='Sec[STRN]')




