from odoo import fields, models, api


class SubBatchSection(models.Model):
    _name = 'sub.batch.section'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', string='Group')
    batch = fields.Many2one(' batch.batch', string='Batch')
    sub_batch_section_line = fields.One2many('sub.batch.section.line', 'sub_batch_section_id')


class SubBatchSectionLine(models.Model):
    _name = 'sub.batch.section.line'

    section = fields.Many2one('section.line', string='Section')
    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', string='Group')
    batch = fields.Many2one(' batch.batch', string='Batch')
    new_sub_batch = fields.Many2one('new.subbatch.line', string='New SubBatch')

    sub_batch_section_id = fields.Many2one('sub.batch.section')



