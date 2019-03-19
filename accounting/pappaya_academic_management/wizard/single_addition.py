from odoo import fields, api, models


class SingleSubject(models.TransientModel):
    _name = 'single.subject'

    name = fields.Char(required=1)
    description = fields.Text()
    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", selection=[('school', 'School'), ('college', 'College')])

    @api.multi
    def create_subjects(self):
        sub_obj = self.env['subject.subject'].search([('academic_year', '=', self.academic_year.id),
                                                      ('institution_type', '=', self.institution_type)], limit=1)
        if sub_obj:
            subject_id = sub_obj.id
        else:
            subject_id = self.env['subject.subject'].create({
                'academic_year': self.academic_year.id,
                'institution_type': self.institution_type
            }).id

        self.env['subject.line'].create({
            'name': self.name,
            'description': self.description,
            'subject_id': subject_id
        })
        return {
            'name': 'Subjects',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'subjects.view',
            'target': 'inline',
        }


class SingleTrack(models.TransientModel):
    _name = 'single.track'

    name = fields.Char(required=1)
    description = fields.Text()
    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", selection=[('school', 'School'), ('college', 'College')])

    @api.multi
    def create_tracks(self):
        track_obj = self.env['pappaya.tracks'].search([('academic_year', '=', self.academic_year.id),
                                                      ('institution_type', '=', self.institution_type)], limit=1)
        if track_obj:
            track_id = track_obj.id
        else:
            track_id = self.env['pappaya.tracks'].create({
                'academic_year': self.academic_year.id,
                'institution_type': self.institution_type
            }).id

        self.env['tracks.line'].create({
            'name': self.name,
            'description': self.description,
            'tracks_id': track_id
        })
        return {
            'name': 'Tracks',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'tracks.view',
            'target': 'inline',
        }


class SingleTopic(models.TransientModel):
    _name = 'single.topic'

    course = fields.Many2one('course.course', string='Course')
    subject = fields.Many2one('subject.line')
    name = fields.Char()
    description = fields.Text()
    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", selection=[('school', 'School'), ('college', 'College')])

    @api.multi
    def create_topics(self):
        topic_obj = self.env['pappaya.topics'].search([('academic_year', '=', self.academic_year.id),
                                                    ('institution_type', '=', self.institution_type)], limit=1)
        if topic_obj:
            topic_id = topic_obj.id
        else:
            topic_id = self.env['pappaya.topics'].create({
                'academic_year': self.academic_year.id,
                'institution_type': self.institution_type,
                'course': self.course.id,
                'subject': self.subject.id
            }).id

        self.env['topics.line'].create({
            'name': self.name,
            'course': self.course.id,
            'subject': self.subject.id,
            'description': self.description,
            'tracks_id': topic_id
        })
        return {
            'name': 'Topics',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'topics.view',
            'target': 'inline',
        }


class SingleSection(models.TransientModel):
    _name = 'single.section'

    name = fields.Char(string='Name')
    from_no = fields.Char('From No')
    to_no = fields.Char('To No')
    description = fields.Text(string='Description')
    course = fields.Many2one('course.course', string='Course')
    group = fields.Many2one('pappaya.group', 'Group')
    batch = fields.Many2one('batch.batch', 'Batch')
    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", selection=[('school', 'School'), ('college', 'College')])

    @api.multi
    def create_sections(self):
        self.env['section.line'].create({
            'name': self.name,
            'course': self.course.id,
            'group': self.group.id,
            'batch': self.batch.id,
            'from_no': self.from_no,
            'to_no': self.to_no,
            'description': self.description,
        })
        return {
            'name': 'Sections',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'pappaya.sections',
            'target': 'inline',
        }


class SinglePreviousCourse(models.TransientModel):
    _name = 'single.previous.course'

    name = fields.Char(string="Course")
    is_external = fields.Boolean(string="External Exam")
    description = fields.Text(string="Description")
    result_entry = fields.Selection(string="Result Entry",
                                    selection=[('manual', 'Manual'), ('results', 'Results'), ])

    academic_year = fields.Many2one('academic.year')
    institution_type = fields.Selection(string="Type", selection=[('school', 'School'), ('college', 'College')])

    @api.multi
    def create_subjects(self):
        if self.academic_year and self.institution_type:
            sub_obj = self.env['previous.course'].search([('academic_year', '=', self.academic_year.id),
                                                      ('institution_type', '=', self.institution_type)], limit=1)
            if sub_obj:
                subject_id = sub_obj.id
            else:
                subject_id = self.env['previous.course'].create({
                    'academic_year': self.academic_year.id,
                    'institution_type': self.institution_type
                }).id

        self.env['courses.line'].create({
            'name': self.name,
            'is_external': self.is_external,
            'description': self.description,
            'result_entry': self.result_entry,
            # 'previous_course_id': subject_id
        })
        return {
            'name': 'Previous Course',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'previous.view',
            'target': 'inline',
        }