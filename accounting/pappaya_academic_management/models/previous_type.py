from odoo import fields, models, api


class PreviousType(models.Model):
    _name = 'previous.type'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    previous_type = fields.One2many('previous.line', 'previous_line_id')


class PreviousLine(models.Model):
    _name = 'previous.line'
    _rec_name = 'name'

    name = fields.Char(string="Previous Type")
    description = fields.Text(string="Description")
    previous_line_id = fields.Many2one('previous.type')

    @api.multi
    def action_create_previous_line(self):
        return {
            'name': 'Previous Type',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'previous.type.view',
            'target': 'inline',
        }