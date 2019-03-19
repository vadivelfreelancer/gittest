from odoo import fields,models,api


class UniversityView(models.TransientModel):
    _name = 'university.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    university_lines = fields.Many2many('university.line')

    @api.model
    def default_get(self, fields):
        res = super(UniversityView, self).default_get(fields)
        university = self.env['university.line'].search([])
        res['university_lines'] = university.ids
        return res


