from odoo import fields, models, api


class BulkUpdate(models.Model):
    _name = 'bulk.update'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    type = fields.Selection(string="Type",default="exam_target", selection=[('exam_target', 'Exam Target'), ('sub_batch', 'Sub Batch'), ])
    from_subbatch = fields.Many2one("subbatch.line", string="From Sub Batch")
    to_subbatch = fields.Many2one("subbatch.line", string="To Sub Batch")
    from_exam = fields.Many2one("exam.target.line", string="From Exam Target")
    to_exam = fields.Many2one("exam.target.line", string="To Exam Target")





