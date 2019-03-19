from odoo import fields, models, api


class PackageSubBatch(models.Model):
    _name = 'package.sub.batch'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', string='Group')
    batch = fields.Many2one(' batch.batch', string='Batch')
    package_sub_batch_line = fields.One2many('package.sub.batch.line', 'package_sub_batch_id')


class SubBatchSectionLine(models.Model):
    _name = 'package.sub.batch.line'

    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', string='Group')
    batch = fields.Many2one(' batch.batch', string='Batch')
    package = fields.Many2one('package.package', string='Package')
    sub_batch = fields.Many2one('subbatch.line', string='SubBatch')

    package_sub_batch_id = fields.Many2one('package.sub.batch')


class Package(models.Model):
    _name = 'package.package'
    _rec_name = 'name'

    name = fields.Char(string="Package")




