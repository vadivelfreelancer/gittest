from odoo import fields, models, api


class TracksView(models.TransientModel):
    _name = 'tracks.view'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    tracks = fields.Many2many('tracks.line', 'track_id')

    @api.model
    def default_get(self, fields):
        res = super(TracksView, self).default_get(fields)
        tracks = self.env['tracks.line'].search([])
        res['tracks'] = tracks.ids
        return res
