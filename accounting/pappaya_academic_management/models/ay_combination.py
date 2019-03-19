from odoo import fields, models, api


class AyCombination(models.Model):
    _name = 'ay.combination'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])

    combination_keys = fields.Many2many('combination.line')
    selected_combinations = fields.Many2many('combination.line')

