from odoo import fields, models


class PappayaSections(models.Model):
    _name = 'pappaya.sections'
    _rec_name = 'course'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one('pappaya.course', string='Course')
    group = fields.Many2one('pappaya.group', 'Group')
    batch = fields.Many2one('pappaya.batch', 'Batch')
    section = fields.Char('Section')


class Batch(models.Model):
    _name = 'batch.batch'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    description = fields.Text(string='Description')


class SectionLine(models.Model):
    _name = 'section.line'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    from_no = fields.Char('From No')
    to_no = fields.Char('To No')
    description = fields.Text(string='Description')
    section_id = fields.Many2one('sections.sections')
    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', 'Group')
    batch = fields.Many2one('batch.batch', 'Batch')
