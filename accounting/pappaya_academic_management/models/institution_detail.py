from odoo import fields, models, api


class AcademicYear(models.Model):
    _name = 'academic.year'

    name = fields.Char(string="Name", required=True)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")


class Subject(models.Model):
    _name = 'subject.subject'
    _rec_name = 'academic_year'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    subjects = fields.One2many('subject.line', 'subject_id')
    batch_mode = fields.Boolean('Batch Mode')

    @api.onchange('batch_mode')
    def onchange_batch(self):
        if self.batch_mode:
            subjects = [(0, 0, {
                'name': '',
                'description': '',
                'subject_id': self.id
            }) for x in range(0, 10)]
            self.subjects = subjects


class SubjectLine(models.Model):
    _name = 'subject.line'

    name = fields.Char()
    description = fields.Text()
    subject_id = fields.Many2one('subject.subject')


class TracksLine(models.Model):
    _name = 'tracks.line'

    name = fields.Char(required=True)
    description = fields.Text()
    tracks_id = fields.Many2one('pappaya.tracks')
