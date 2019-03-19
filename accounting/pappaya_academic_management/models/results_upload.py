from odoo import fields, models, api


class ResultUpload(models.Model):
    _name = 'result.upload'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    pre_course = fields.Many2one('courses.line', string='Previous Course')






