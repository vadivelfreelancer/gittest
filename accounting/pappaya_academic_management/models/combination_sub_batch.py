from odoo import fields, models, api


class CombinationSubBatch(models.Model):
    _name = 'combination.sub.batch'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    combination = fields.Many2one('combination.combination', string='')
    combination_subbatch_line = fields.One2many('combination.sub.line', 'combination_sb_id')


class combinationSubBatchLine(models.Model):
    _name = 'combination.sub.line'
    combination = fields.Many2one('combination.combination', string='')
    sub_batch = fields.Many2one('sub.batch', string="Sub Batch")
    # status = fields.Selection(string="Status", selection=[('open', 'Open'), ('closed', 'Closed'), ])
    status = fields.Boolean(string="Status")
    description = fields.Text(string="Description")
    combination_sb_id = fields.Many2one('combination.sub.batch')

    @api.multi
    def action_create_combination_line(self):
        return {
            'name': 'Combination Wise Subbatch',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'combination.sub.view',
            'target': 'inline',
        }