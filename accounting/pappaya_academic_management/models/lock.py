from odoo import fields, models, api


class Lock(models.Model):
    _name = 'lock.lock'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    sub_batch = fields.Many2one('sub.batch', string='Sub Batch')
    sub_section = fields.Many2one('sub.section', string='Group')
    lock_line = fields.One2many('lock.line', 'lock_id')


class LockLine(models.Model):
    _name = 'lock.line'

    hyd_dn = fields.Boolean(string="HYD-DN")
    adoni = fields.Boolean(string="ADONI")
    lock_id = fields.Many2one('lock.lock')

    # @api.multi
    # def action_create_pc_subject_line(self):
    #     return {
    #         'name': 'Previous Course Subjects',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'view_type': 'form',
    #         'res_model': 'previous.course.subject.view',
    #         'target': 'inline',
    #     }