from odoo import fields, models


class EtWiseCombination(models.Model):
    _name = 'et.wise.combination'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    select_all = fields.Boolean("Check All/ Uncheck All")
    exam_type = fields.Many2one('exam.type.line', string='Exam Type')
    combinations = fields.Many2many('combination.line')
