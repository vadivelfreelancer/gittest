from odoo import fields, models, api


class CourseGroupBatchSub(models.Model):
    _name = 'cg.batch.sub'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', string='Group')
    batch = fields.Many2one('batch.batch', string='Batch')
    cg_batch_line = fields.One2many('cg.batch.line', 'cg_batch_id')


class CourseGroupBatchLine(models.Model):
    _name = 'cg.batch.line'

    sub_batch = fields.Many2one('sub.batch', string="Sub Batch")
    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', string='Group')
    batch = fields.Many2one('batch.batch', string='Batch')
    description = fields.Text(string="Description")
    cg_batch_id = fields.Many2one('cg.batch.sub')

    @api.multi
    def action_create_course_group_line(self):
        return {
            'name': 'Course Group Batch Sub Batch',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'cg.batch.sb.view',
            'target': 'inline',
        }