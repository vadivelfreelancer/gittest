# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm, ValidationError
import re
from datetime import datetime


class admission_target_allocation(models.Model):
    _name = 'admission.target.allocation'
    _rec_name = 'course_package_id'

    academic_year_id = fields.Many2one('academic.year', 'Academic Year', track_visibility='onchange',
                                       default=lambda self: self.env['academic.year'].search(
                                           [('is_active', '=', True)]))
    course_package_id = fields.Many2one('pappaya.course.package', 'Course Package')
    branch_id = fields.Many2one('operating.unit', 'Branch')
    target_count = fields.Integer('Target Count')

    @api.constrains('academic_year_id', 'course_package_id', 'branch_id', 'target_count')
    def validate_constraints(self):
        if self.sudo().search_count([('academic_year_id', '=', self.academic_year_id.id),
                                     ('course_package_id', '=', self.course_package_id.id),
                                     ('branch_id', '=', self.branch_id.id)]) > 1:
            raise ValidationError('Record already exists for given combination!.')
        if not self.target_count > 0:
            raise ValidationError('Target Count should be greater than 0')

    @api.onchange('branch_id', 'academic_year_id', 'course_package_id')
    def onchange_branch_id(self):
        domain = {};
        domain['course_package_id'] = [('id', 'in', [])];
        course_pkg_ids = []
        if self.branch_id and self.academic_year_id:
            course_config_obj = self.env['pappaya.branch.ay.course.config'].search(
                [('operating_unit_id', '=', self.branch_id.id),
                 ('active', '=', True), ('academic_year_id', '=', self.academic_year_id.id)], limit=1)
            course_pkg_ids = course_config_obj.course_package_ids.ids
            if course_pkg_ids:
                domain['course_package_id'] = [('id', 'in', course_pkg_ids)]
        return {'domain': domain}


class lock_in_fee_slab(models.Model):
    _name = 'lock.in.fee.slab'

    @api.multi
    def _compute_active_slab(self):
        for record in self:
            target_count = 0.0
            if record.fee_structure_id:
                course_package_id = self.env['pappaya.course.package'].search(
                    [('course_id', '=', record.fee_structure_id.course_id.id),
                     ('group_id', '=', record.fee_structure_id.group_id.id),
                     ('batch_id', '=', record.fee_structure_id.batch_id.id),
                     ('package_id', '=', record.fee_structure_id.package_id.id)], limit=1)

                target_count = self.env['admission.target.allocation'].search(
                    [('academic_year_id', '=', record.fee_structure_id.academic_year_id.id),
                     ('course_package_id', '=', course_package_id.id),
                     ('branch_id', '=', record.fee_structure_id.school_id.id)]).target_count

                admission_count = self.env['pappaya.admission'].search_count(
                    [('academic_year', '=', record.fee_structure_id.academic_year_id.id),
                     ('package_id', '=', course_package_id.id),
                     ('branch_id', '=', record.fee_structure_id.school_id.id),
                     ('stage_id.sequence', '>=', 3)])

                if target_count > 0:
                    target_percentage = 100 * admission_count / target_count
                    if record.percentage_from <= target_percentage <= record.percentage_to:
                        record.is_active = True
                    elif target_percentage > 100 and record.percentage_to == 100.0:
                        record.is_active = True
                else:
                    record.is_active = False
            else:
                record.is_active = False

    fee_structure_id = fields.Many2one('pappaya.fees.structure', 'Fee Structure')
    percentage_from = fields.Float('From %')
    percentage_to = fields.Float('To %')
    locked_amount_new = fields.Float('Lock in amount for \n New Student')
    locked_amount_old = fields.Float('Lock in amount for \n Old Student')
    is_active = fields.Boolean(compute='_compute_active_slab', string='Is Active')
    state = fields.Selection(selection=[('draft', 'Draft'), ('confirm', 'Confirm'),
                                        ('review', 'Reviewed'), ('approve', 'Approve'), ('validate', 'Validate'),
                                        ('archive', 'Locked')], string='State', default='draft')

    @api.onchange('locked_amount_new')
    def onchange_locked_amount_new(self):
        if self.locked_amount_new and self.locked_amount_new < 0:
            raise ValidationError('Lock in amount for New Student should not be less than zero')

    @api.onchange('locked_amount_old')
    def onchange_locked_amount_old(self):
        if self.locked_amount_old and self.locked_amount_old < 0:
            raise ValidationError('Lock in amount for Old Student should not be less than zero')


class Pappaya_fees_structure(models.Model):
    _name = 'pappaya.fees.structure'
    _inherit = ['mail.thread', 'resource.mixin']

    @api.constrains('lock_in_fee_slab_ids')
    def check_lock_in_fee_slab_ids(self):
        for record in self:
            course_fee_new = course_fee_old = 0.0
            for fee_line in record.structure_line_ids:
                if fee_line.fees_id.is_course_fee:
                    course_fee_new = fee_line.new_total;
                    course_fee_old = fee_line.total
            for line in record.lock_in_fee_slab_ids:
                if line.locked_amount_new > course_fee_new:
                    raise ValidationError(_("Given Lock in amount (%s) should not be excceded than course fee (%s)") % (
                    line.locked_amount_new, course_fee_new))
                elif line.locked_amount_old > course_fee_old:
                    raise ValidationError(_("Given Lock in amount (%s) should not be excceded than course fee (%s)") % (
                    line.locked_amount_old, course_fee_old))
                if line.percentage_from == line.percentage_to:
                    raise ValidationError("From percentage and To percentage should not be same.")
                if not line.percentage_from >= 0.0 or not line.percentage_to > 0.0:
                    raise ValidationError("Lock in amount slab percentage should be greater than zero")
                elif line.percentage_from > 100.0 or line.percentage_to > 100.0:
                    raise ValidationError("Lock in amount slab percentage should not be exceeded than 100 %")
                for loop_line in record.lock_in_fee_slab_ids:
                    if loop_line.id != line.id:
                        if line.percentage_from == loop_line.percentage_from or line.percentage_from == loop_line.percentage_to:
                            raise ValidationError(
                                _("Given Percentage From ( %s ) Already configured in slabs.") % line.percentage_from)
                        if line.percentage_to == loop_line.percentage_to or line.percentage_to == loop_line.percentage_from:
                            raise ValidationError(
                                _("Given Percentage From ( %s ) Already configured in slabs.") % line.percentage_to)

                        if line.percentage_from > loop_line.percentage_from and line.percentage_from < loop_line.percentage_to:
                            raise ValidationError(
                                _("Given Percentage From ( %s ) Already configured in slabs.") % line.percentage_from)
                        elif line.percentage_to > loop_line.percentage_from and line.percentage_to < loop_line.percentage_to:
                            raise ValidationError(
                                _("Given Percentage To ( %s ) Already configured in slabs.") % line.percentage_to)
            return True

    @api.constrains('structure_line_ids')
    def validate_course_fee(self):
        is_course_fee = False
        for line in self.structure_line_ids:
            if line.fees_id.is_course_fee:
                is_course_fee = True
        if not is_course_fee:
            raise ValidationError("Course fee should be configured in Fee Structure Line.")

    @api.multi
    def _compute_is_lock_fee_structure(self):
        for record in self:
            for lock_slab in record.lock_in_fee_slab_ids:
                if lock_slab.is_active and lock_slab.percentage_to == 100.0:
                    record.is_lock_fee_structure = True
                    self._cr.execute("update pappaya_fees_structure set state='archive' where id = %s" % record.id)
                    self._cr.execute(
                        "update pappaya_fees_structure_line set state='archive' where structure_id= %s" % record.id)
                    self._cr.execute(
                        "update lock_in_fee_slab set state='archive' where fee_structure_id = %s" % record.id)
                    self._cr.commit()
                else:
                    record.is_lock_fee_structure = False

    @api.multi
    def action_confirm(self):
        for record in self:
            record.structure_line_ids.write({'state': 'confirm'})
            record.state = 'confirm'
            record.lock_in_fee_slab_ids.write({'state': 'confirm'})

    @api.multi
    def action_review(self):
        for record in self:
            record.structure_line_ids.write({'state': 'review'})
            record.state = 'review'
            record.lock_in_fee_slab_ids.write({'state': 'review'})

    @api.multi
    def action_approve(self):
        for record in self:
            record.structure_line_ids.write({'state': 'approve'})
            record.state = 'approve'
            record.lock_in_fee_slab_ids.write({'state': 'approve'})

    @api.multi
    def action_validate(self):
        for record in self:
            record.structure_line_ids.write({'state': 'validate'})
            record.state = 'validate'
            record.lock_in_fee_slab_ids.write({'state': 'validate'})

    @api.multi
    def action_reset(self):
        for record in self:
            record.structure_line_ids.write({'state': 'draft'})
            record.state = 'draft'
            record.lock_in_fee_slab_ids.write({'state': 'draft'})

    name = fields.Char('Name', size=128, track_visibility='onchange')
    academic_year_id = fields.Many2one('academic.year', 'Academic Year', track_visibility='onchange',
                                       default=lambda self: self.env['academic.year'].search(
                                           [('is_active', '=', True)]))
    school_id = fields.Many2one('operating.unit', 'Branch', track_visibility='onchange')
    entity_id = fields.Many2one(comodel_name='operating.unit', related='school_id.parent_id', string='Entity',
                                track_visibility='onchange')
    residential_type_id = fields.Many2one('residential.type', 'Student Residential Type', track_visibility='onchange')
    student_type = fields.Selection([('day', 'Day'), ('semi_residential', 'Semi Residential'), ('hostel', 'Hostel')],
                                    default='day', string='Student Type', track_visibility='onchange')
    course_id = fields.Many2one('pappaya.course', 'Course', track_visibility='onchange')
    type = fields.Selection(
        selection=[('short_term', 'Short Term'), ('long_term', 'Long Term'), ('coaching_centre', 'Coaching Centre')],
        related='course_id.type', string='Type',
        track_visibility='onchange')
    group_id = fields.Many2one('pappaya.group', "Group", track_visibility='onchange')
    batch_id = fields.Many2one('pappaya.batch', 'Batch', track_visibility='onchange')
    package_id = fields.Many2one('pappaya.package', 'Package', track_visibility='onchange')
    medium_id = fields.Many2one('pappaya.master', 'Medium', track_visibility='onchange')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('both', 'Both')], default='male',
                              track_visibility='onchange')
    structure_line_ids = fields.One2many('pappaya.fees.structure.line', 'structure_id', track_visibility='onchange')
    total_amount = fields.Float('Total Amount', compute="_get_total_amount")
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('confirm', 'Confirmed'), ('review', 'Reviewed'), ('approve', 'Approve'),
                   ('validate', 'Validate'), ('archive', 'Locked')],
        string='State', default='draft', track_visibility='onchange')
    lock_in_fee_slab_ids = fields.One2many('lock.in.fee.slab', 'fee_structure_id', 'Lock in amount Slab',
                                           track_visibility='onchange')
    is_tax_applicable = fields.Boolean(compute='_compute_is_tax_applicable', string='Is tax applicable?')
    is_lock_fee_structure = fields.Boolean(compute='_compute_is_lock_fee_structure', string='Is Lock Fee Structure')
    amt_old_student = fields.Float('Total Old Student', compute='compute_amt_old_student')
    amt_new_student = fields.Float('Total New Student', compute='compute_amt_new_student')

    @api.multi
    @api.depends('structure_line_ids.total')
    def compute_amt_old_student(self):
        for rec in self:
            tot = 0.0
            for line in rec.structure_line_ids:
                if line.fees_id.is_course_fee and line.fees_id.is_course_fee_component or line.fees_id.is_reservation_fee:
                    tot += line.total
            total = round(sum(line.total for line in rec.structure_line_ids))
            rec.amt_old_student = total - tot

    @api.multi
    @api.depends('structure_line_ids.new_stud_amount')
    def compute_amt_new_student(self):
        for rec in self:
            tot = 0.0
            for line in rec.structure_line_ids:
                if line.fees_id.is_course_fee and line.fees_id.is_course_fee_component or line.fees_id.is_reservation_fee:
                    tot += line.new_stud_amount
            total = round(sum(line.new_stud_amount for line in rec.structure_line_ids))
            rec.amt_new_student = total - tot

    @api.multi
    @api.depends('entity_id')
    def _compute_is_tax_applicable(self):
        for record in self:
            record.is_tax_applicable = True if record.entity_id.is_tax_applicable else False

    @api.depends('structure_line_ids')
    def _get_total_amount(self):
        if self.structure_line_ids:
            amount = 0.00
            for line in self.structure_line_ids:
                amount += line.amount
            if amount:
                self.total_amount = amount

    @api.onchange('structure_line_ids')
    def onchange_structure_line_ids(self):
        total = 0.0;
        new_stud_amount = 0.0
        for line in self.structure_line_ids:
            if not line.fees_id.is_course_fee and line.fees_id.is_course_fee_component:
                total += line.total;
                new_stud_amount += line.new_stud_amount
        for course_line in self.structure_line_ids:
            if course_line.fees_id.is_course_fee:
                course_line.total = course_line.amount = total
                course_line.new_stud_amount = course_line.new_total = new_stud_amount
                break;

    @api.one
    @api.constrains('name')
    def check_name(self):
        if len(self.search([('name', '=ilike', self.name)])) > 1:
            raise ValidationError('Fee Structure Name already exists')

    @api.one
    @api.constrains('academic_year_id', 'school_id', 'residential_type_id', 'course_id', 'group_id', 'batch_id',
                    'package_id')
    def check_fees_struct(self):
        if self.sudo().search_count(
                [('academic_year_id', '=', self.academic_year_id.id), ('school_id', '=', self.school_id.id),
                 ('residential_type_id', '=', self.residential_type_id.id), ('course_id', '=', self.course_id.id),
                 ('group_id', '=', self.group_id.id),
                 ('batch_id', '=', self.batch_id.id), ('package_id', '=', self.package_id.id)]) > 1:
            raise ValidationError('Fee Structure already exists')

    @api.constrains('structure_line_ids', 'structure_line_ids.sequence_no', 'structure_line_ids.less_sequence',
                    'structure_line_ids.min_amount', 'structure_line_ids.new_stud_min_amount')
    def check_sequence_no(self):
        sequence_numbers = []
        for rec in self.structure_line_ids:
            # Validation for less sequence
            if rec.less_sequence > 0:
                if rec.less_sequence not in sequence_numbers:
                    sequence_numbers.append(rec.less_sequence)
                elif rec.less_sequence in sequence_numbers:
                    raise ValidationError("Less sequence should be unique!")
            # Validation for pay sequence
            if rec.sequence_no <= 0:
                raise ValidationError('Please enter Sequence..!')
            num_list = []
            for num in self.env['pappaya.fees.structure.line'].search([('structure_id', '=', self.id)]):
                num_list.append(num.sequence_no)
            if (len(num_list)) != (len(set(num_list))):
                raise ValidationError('Pay Sequence should be unique..!')
            if rec.min_amount:
                if rec.min_amount > rec.v_amount:
                    raise ValidationError(
                        _("For OLD Student : \nLock-In Amount(%s) should not be greater than the Total amount(%s).") % (
                            rec.min_amount, rec.v_amount))
            if rec.new_stud_min_amount:
                if rec.new_stud_min_amount > rec.new_total:
                    raise ValidationError(
                        _("For New Student : \nLock-In Amount(%s) should not be greater than the Total amount(%s).") % (
                            rec.new_stud_min_amount, rec.new_total))

    #     @api.constrains('school_id','structure_line_ids.fees_id')
    #     def check_transport_fee_head(self):
    #         if self.school_id and self.school_id.is_transport:
    #             transport = [line.id for line in self.structure_line_ids if line.fees_id.is_transport_fee]
    #             if not transport:
    #                 raise ValidationError('Please configure the Transport Fee for the current branch..!')
    #             else:
    #                 if len(transport) > 1:
    #                     raise ValidationError('Transport Fee already exist..!')
    #
    #     @api.constrains('school_id', 'structure_line_ids.fees_id')
    #     def check_nslate_fee_head(self):
    #         if self.school_id and self.school_id.is_nslate:
    #             nslate = [line.id for line in self.structure_line_ids if line.fees_id.is_nslate_fee]
    #             if not nslate:
    #                 raise ValidationError('Please configure the Nslate Fee for the current branch..!')
    #             else:
    #                 if len(nslate) > 1:
    #                     raise ValidationError('Nslate Fee already exist..!')

    @api.onchange('academic_year_id', 'school_id')
    def onchange_academic_year_id(self):
        self.course_id = False;
        self.residential_type_id = False
        domain = {}
        if self.academic_year_id and self.school_id:
            course_ids = self.env['pappaya.branch.ay.course.config'].search(
                [('operating_unit_id', '=', self.school_id.id),
                 ('active', '=', True), ('academic_year_id', '=', self.academic_year_id.id)]).mapped(
                'course_package_ids').mapped('course_id').ids
            domain['course_id'] = [('id', 'in', course_ids)]
            domain['residential_type_id'] = [('id', 'in', self.school_id.residential_type_ids.ids)]
        return {'domain': domain}

    @api.onchange('course_id')
    def onchange_course_id(self):
        domain = []
        if self.academic_year_id and self.school_id and self.course_id:
            for academic in self.env['pappaya.branch.ay.course.config'].search(
                    [('operating_unit_id', '=', self.school_id.id), ('active', '=', True),
                     ('academic_year_id', '=', self.academic_year_id.id)]):
                for course_package in academic.course_package_ids:
                    if course_package.course_id.id == self.course_id.id:
                        domain.append(course_package.group_id.id)
        self.previous_fee_head_pop()
        return {'domain': {'group_id': [('id', 'in', domain)]}}

    @api.onchange('group_id')
    def onchange_group_id(self):
        domain = []
        if self.academic_year_id and self.school_id:
            for academic in self.env['pappaya.branch.ay.course.config'].search(
                    [('operating_unit_id', '=', self.school_id.id), ('active', '=', True),
                     ('academic_year_id', '=', self.academic_year_id.id)]):
                for course_package in academic.course_package_ids:
                    if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id:
                        domain.append(course_package.batch_id.id)
        self.previous_fee_head_pop()
        return {'domain': {'batch_id': [('id', 'in', domain)]}}

    @api.onchange('batch_id')
    def onchange_batch_id(self):
        domain = []
        if self.academic_year_id and self.school_id and self.course_id and self.group_id and self.batch_id:
            for academic in self.env['pappaya.branch.ay.course.config'].search(
                    [('operating_unit_id', '=', self.school_id.id), ('active', '=', True),
                     ('academic_year_id', '=', self.academic_year_id.id)]):
                for course_package in academic.course_package_ids:
                    if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id and course_package.batch_id.id == self.batch_id.id:
                        domain.append(course_package.package_id.id)
        self.previous_fee_head_pop()
        return {'domain': {'package_id': [('id', 'in', domain)]}}

    @api.onchange('residential_type_id')
    def onchange_residential_type_id(self):
        self.previous_fee_head_pop()

    """Method to populate fee head and amount depends on cgbp combination"""

    def previous_fee_head_pop(self):
        self.structure_line_ids = False
        if self.school_id and self.academic_year_id and self.course_id and self.residential_type_id:
            default_heads = self.env['pappaya.fees.head'].sudo().search(
                [('is_show_by_default', '=', True), ('residential_type_ids', 'in', [self.residential_type_id.id])])
            previous_heads = [];
            head_ids_previous = [];
            seq_no = 0
            org_fee_struc_ids_search = self.sudo().search([('school_id', '=', self.school_id.id),
                                                           ('academic_year_id', '=', self.academic_year_id.id),
                                                           ('course_id', '=', self.course_id.id),
                                                           ('group_id', '=',
                                                            self.group_id.id if self.group_id.id else False),
                                                           ('batch_id', '=',
                                                            self.batch_id.id if self.batch_id.id else False),
                                                           ('package_id', '=',
                                                            self.package_id.id if self.package_id else False),
                                                           ('residential_type_id', '=', self.residential_type_id.id)
                                                           ])
            for structure in org_fee_struc_ids_search:
                for stuct_line in structure.structure_line_ids:
                    seq_no += 1
                    head_ids_previous.append(stuct_line.fees_id.id)
                    previous_heads.append((0, 0, {'course_id': self.course_id.id,
                                                  'fees_id': stuct_line.fees_id.id,
                                                  'readonly': True if stuct_line.fees_id.is_course_fee else False,
                                                  'description': stuct_line.description,
                                                  'amount': stuct_line.amount,
                                                  'min_amount': stuct_line.min_amount,
                                                  'percentage': stuct_line.percentage,
                                                  'sequence_no': seq_no,
                                                  'less_sequence': stuct_line.less_sequence,
                                                  'state': 'draft'
                                                  }))
            for default_head in default_heads:
                seq_no += 1
                if default_head.id not in head_ids_previous:
                    previous_heads.append((0, 0, {'course_id': self.course_id.id,
                                                  'fees_id': default_head.id,
                                                  'readonly': True if default_head.is_course_fee else False,
                                                  'amount': 0.00,
                                                  'min_amount': 0.00,
                                                  'percentage': 0.00,
                                                  'sequence_no': seq_no,
                                                  'state': 'draft'
                                                  }))

            self.structure_line_ids = previous_heads


class PappayaFeeStructureLine(models.Model):
    _name = 'pappaya.fees.structure.line'
    _description = "Pappaya Fees Structure Line"
    _order = 'sequence_no asc'

    @api.multi
    def _compute_total_tax(self):
        for record in self:
            record.total_tax = 0.0
            record.new_total_tax = 0.0

    structure_id = fields.Many2one('pappaya.fees.structure')
    fees_id = fields.Many2one('pappaya.fees.head', 'Fee Type')
    description = fields.Char('Description')
    percentage = fields.Float('Admission Minimum percentage')
    locked_amount = fields.Float('Admission Min Amount')
    readonly = fields.Boolean('Readonly', default=False)
    course_id = fields.Many2one('pappaya.course', 'Course')
    sequence_no = fields.Integer(string='Pay\nSequence')
    less_sequence = fields.Integer('Less\nSequecne')
    # Old student
    concession_percent_old = fields.Integer('Concession for Old Student(%)')
    min_amount = fields.Float('Lock-In Amount for Old Student')
    amount = fields.Float('Total Amount')

    tax_ids = fields.Many2many(comodel_name='account.tax', string='Taxes')
    cgst = fields.Float('CGST')
    sgst = fields.Float('SGST')
    igst = fields.Float('IGST')
    total_tax = fields.Float(compute='_compute_total_tax', string='Total Tax')
    total = fields.Float('Amount for Old Student')
    # Taxes for new students

    concession_percent_new = fields.Integer('Concession for New Student(%)')
    new_stud_amount = fields.Float('Amount for New Student')
    new_stud_min_amount = fields.Float('Lock-In Amount for New Student')
    new_tax_ids = fields.Many2many(comodel_name='account.tax', string='Taxes')
    new_cgst = fields.Float('CGST')
    new_sgst = fields.Float('SGST')
    new_igst = fields.Float('IGST')
    new_total_tax = fields.Float(compute='_compute_total_tax', string='Total Tax')
    new_total = fields.Float('Total for New Student', compute='_get_new_gstvalue')

    v_cgst = fields.Char('CGST', compute='_get_gstvalue')
    v_sgst = fields.Char('SGST', compute='_get_gstvalue')
    v_amount = fields.Float('Total for Old Student', compute='_get_gstvalue')

    n_cgst = fields.Float('CGST')
    n_sgst = fields.Float('SGST')
    n_amount = fields.Float('Amount')
    new_cgst = fields.Char('CGST', compute='_get_new_gstvalue')
    new_sgst = fields.Char('SGST', compute='_get_new_gstvalue')

    state = fields.Selection(
        selection=[('draft', 'Draft'), ('confirm', 'Confirmed'), ('review', 'Reviewed'), ('approve', 'Approve'),
                   ('validate', 'Validate'), ('archive', 'Locked')], string='State', default='draft')

    @api.onchange('new_stud_amount')
    def onchange_new_stud_amount(self):
        if self.new_stud_amount and self.new_stud_amount < 0:
            raise ValidationError('Amount for New Student should not be less than zero')

    @api.onchange('total')
    def onchange_total(self):
        if self.total and self.total < 0:
            raise ValidationError('Amount for Old Student should not be less than zero')

    @api.multi
    def action_confirm(self):
        for record in self:
            record.state = 'confirm'

    @api.multi
    def action_review(self):
        for record in self:
            record.state = 'review'

    @api.multi
    def action_approve(self):
        for record in self:
            record.state = 'approve'

    @api.multi
    def action_validate(self):
        for record in self:
            record.state = 'validate'

    @api.multi
    def action_reset(self):
        for record in self:
            record.state = 'draft'

    #     @api.one
    #     @api.constrains('fees_id')
    #     def check_fees(self):
    #         for rec in self:
    #             if not (rec.structure_id.school_id.student_type in ['hostel','both'] and rec.structure_id.school_id.is_caution_deposit):
    #                 if rec.fees_id.is_caution_deposit_fee:
    #                     raise ValidationError('Please enable the Caution Deposit in Branch..!')
    #
    #             if len(self.search(
    #                     [('structure_id', '=', self.structure_id.id),
    #                      ('fees_id', '=', self.fees_id.id)])) > 1:
    #                 raise ValidationError('Fee Head is already exists')
    #
    #     @api.one
    #     @api.constrains('new_stud_amount')
    #     def check_fees_amount(self):
    #         if self.fees_id.is_course_fee:
    #             if self.new_stud_amount <= 0:
    #                 raise ValidationError('Amount Should be greater than zero')

    #     @api.one
    #     @api.constrains('total','min_amount','new_stud_min_amount')
    #     def check_numeric_validation(self):
    #         if self.total:
    #             if self.total < 0.0:
    #                 raise ValidationError('Please enter the valid values')
    #         if self.min_amount :
    #             if self.min_amount > self.v_amount:
    #                 raise ValidationError(_("For OLD Student : \nLock-In Amount(%s) should not be greater than the Total amount(%s).") % (
    #                                         self.min_amount, self.v_amount))
    #
    #             if self.min_amount < 0.0:
    #                 raise ValidationError('Please enter the valid values')
    #         if self.new_stud_min_amount:
    #             if self.new_stud_min_amount > self.new_total:
    #                 raise ValidationError(_("For New Student : \nLock-In Amount(%s) should not be greater than the Total amount(%s).") % (
    #                                         self.new_stud_min_amount, self.new_total))
    #             if self.new_stud_min_amount < 0.0:
    #                 raise ValidationError('Please enter the valid values')
    #
    #     @api.one
    #     @api.constrains('concession_percent_old', 'concession_percent_new')
    #     def check_concession_percentage(self):
    #         for rec in self:
    #             if (rec.concession_percent_old and rec.concession_percent_old > 100) or (rec.concession_percent_new and rec.concession_percent_new > 100):
    #                 raise ValidationError('Concession should not exceeds 100%')
    #             elif (rec.concession_percent_old and rec.concession_percent_old < 0) or (rec.concession_percent_new and rec.concession_percent_new < 0):
    #                 raise ValidationError('Concession percentage should not be negative')

    @api.multi
    @api.depends('sgst', 'cgst', 'amount')
    def _get_gstvalue(self):
        for record in self:
            if record.sgst:
                record.v_sgst = str(record.sgst)
            if record.cgst:
                record.v_cgst = str(record.cgst)
            if record.amount:
                record.v_amount = record.amount

    @api.multi
    @api.depends('n_sgst', 'n_cgst', 'n_amount')
    def _get_new_gstvalue(self):
        for record in self:
            if record.n_sgst:
                record.new_sgst = str(record.n_sgst)
            if record.n_cgst:
                record.new_cgst = str(record.n_cgst)

            if record.new_stud_amount:
                record.new_total = record.new_stud_amount

    @api.onchange('fees_id')
    def onchange_fees_head(self):
        if self.fees_id:
            self.total = self.v_amount = self.new_stud_amount = self.min_amount = self.new_stud_min_amount = None
            self.course_id = self.structure_id.course_id.id
            total = 0.0; total_new = 0.0
            course_line = False
            for line in self.structure_id.structure_line_ids:
                if line.fees_id.is_course_fee:
                    course_line = line
                if line.fees_id.is_course_fee_component:
                    total += line.amount
                    total_new += line.new_total
            if course_line:
                course_line.amount = total
                course_line.new_total = total_new
            if self.fees_id.is_course_fee:
                self.readonly = True
            else:
                self.readonly = False

    @api.onchange('sgst', 'cgst', 'total')
    def onchange_gst(self):
        self.sgst = 0
        self.cgst = 0
        self.amount = 0
        if self.total:
            if self.course_id.sgst:
                self.sgst = (self.total * self.course_id.sgst) / 100
            if self.course_id.cgst:
                self.cgst = (self.total * self.course_id.cgst) / 100
            self.amount = self.sgst + self.cgst + self.total
            self.v_sgst = str(self.sgst)
            self.v_cgst = str(self.cgst)
            self.v_amount = self.amount

    @api.onchange('n_sgst', 'n_cgst', 'new_stud_amount')
    def _onchange_new_gst(self):
        self.n_sgst = 0
        self.n_cgst = 0
        self.n_amount = 0
        if self.new_stud_amount:
            if self.course_id.sgst:
                self.n_sgst = (self.new_stud_amount * self.course_id.sgst) / 100
            if self.course_id.cgst:
                self.n_cgst = (self.new_stud_amount * self.course_id.cgst) / 100
            self.n_amount = self.n_sgst + self.n_cgst + self.new_stud_amount
            self.new_sgst = str(self.sgst)
            self.new_cgst = str(self.cgst)
            self.new_total = self.n_amount
