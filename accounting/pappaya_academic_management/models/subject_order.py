from odoo import fields, models


class SubjectOrder(models.Model):
    _name = 'subject.order'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', string="Academic Year")
    institution_type = fields.Selection(string="Type", default="school",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    subject_type_collage = fields.One2many('subjectorder.line.collage', 'subject_order_id')
    subject_type_school = fields.One2many('subjectorder.line.school', 'subject_order_id')


class SubjectOrderCollageLine(models.Model):
    _name = 'subjectorder.line.collage'
    _rec_name = 'name'

    name = fields.Char(string="Subject")
    rep_order = fields.Integer(string="Rep.Order")
    jr_order = fields.Integer(string="Jr.Order")
    sr_order = fields.Integer(string="Sr.Order")
    ssc_order = fields.Integer(string="SSC.Order")
    subject_order_id = fields.Many2one('subject.order')


class SubjectOrderSchoolLine(models.Model):
    _name = 'subjectorder.line.school'
    _rec_name = 'name'

    name = fields.Char(string="Subject")
    rep_order = fields.Integer(string="Rep.Order")
    subject_order_id = fields.Many2one('subject.order')
