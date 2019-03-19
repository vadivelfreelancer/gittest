from odoo import fields, models


class AreaWiseBranch(models.Model):
    _name = 'area.wise.branch'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    select_all = fields.Boolean("Check All/ Uncheck All")
    area = fields.Many2one('area.line', string='Area')
    branches = fields.Many2many('branch.branch')
