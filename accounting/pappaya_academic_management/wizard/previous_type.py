from odoo import fields, models, api


class PreviousTypeView(models.TransientModel):
    _name = 'previous.type.view'

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    previous = fields.Many2many('previous.line')

    @api.model
    def default_get(self, fields):
        res = super(PreviousTypeView, self).default_get(fields)
        previous = self.env['previous.line'].search([])
        res['previous'] = previous.ids
        return res
