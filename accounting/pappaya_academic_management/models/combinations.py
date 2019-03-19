from odoo import fields,models,api


class CombinationCombination(models.Model):
    _name = 'combination.combination'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'),])
    course = fields.Many2one('course.course', string='Course')
    combination_line_line = fields.One2many('combination.line', 'combination_id')


class CombinationLine(models.Model):
    _name = 'combination.line'
    _rec_name = 'name'

    name = fields.Char()
    description = fields.Text(string="Description")
    group = fields.Many2one('pappaya.group', 'Group')
    exam_type = fields.Many2one('exam.type', 'Exam Type')
    course = fields.Many2one('course.course', string='Course')
    combination_id = fields.Many2one("combination.combination", string="Combination")

    @api.multi
    def action_create_combination_line(self):
        return {
            'name': 'Combinations',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'combination.view',
            'target': 'inline',
        }
