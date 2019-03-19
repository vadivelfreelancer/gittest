from odoo import api, fields, models


class BranchMappingWithDivision(models.Model):
    _name = 'branch.mapping.with.division'

    academic_year = fields.Many2one('academic.year', 'Academic Year')
    institution_type = fields.Selection(string="Type",
                                        selection=[('school', 'School'), ('college', 'College'), ])
    state = fields.Many2one("res.country.state", string="State")
    district = fields.Many2one("state.district", string="District")
    division = fields.Many2one("division.line", string="Division")
    branch_search = fields.Char(string="Branch Search")
    mapping_lines = fields.One2many("branch.mapping.line", "branch_mapping_id", string="")


# class District(models.Model):
#     _name = 'state.district'
#     _rec_name = 'name'
#     _description = 'District'
# 
#     name = fields.Char()


class BrachMappingLine(models.Model):
    _name = 'branch.mapping.line'
    _description = ''

    exam_branch = fields.Many2one('exam.branch', string="Exam Branch  ")
    division = fields.Many2one("division.line", string="Division")
    zone = fields.Many2one("district.zone", string="Zone")
    do = fields.Many2one("zone.do", string="Do")
    branch_mapping_id = fields.Many2one("branch.mapping.with.division", string="")


class DistrictZone(models.Model):
    _name = 'district.zone'
    _rec_name = 'name'

    name = fields.Char()


class ZoneDo(models.Model):
    _name = 'zone.do'
    _rec_name = 'name'

    name = fields.Char()

