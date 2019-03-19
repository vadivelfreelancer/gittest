from odoo import fields,models,api


class AreaView(models.TransientModel):
    _name = 'area.view'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    area_lines = fields.Many2many('area.line')

    @api.model
    def default_get(self, fields):
        res = super(AreaView, self).default_get(fields)
        area = self.env['area.line'].search([])
        res['area_lines'] = area.ids
        return res


