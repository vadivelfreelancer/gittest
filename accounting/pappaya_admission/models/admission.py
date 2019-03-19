# -*- coding: utf-8 -*-
import re
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

import odoo.addons.decimal_precision as dp
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class PappayaAdmission(models.Model):
    _name = "pappaya.admission"
    _rec_name = 'student_full_name'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [('student_full_name', operator, name), ('res_no', operator, name)]
        else:
            domain = ['|', ('student_full_name', operator, name), ('res_no', operator, name)]
            objs = self.search(expression.AND([domain, args]), limit=limit)
        return objs.name_get()

    @api.one
    @api.constrains('talent_exam_id', 'is_exam_attended', 'admission_no','res_no')
    def _check_talent_exam_id(self):
        if self.is_exam_attended == 'yes' and self.talent_exam_id:
            if len(self.search([('talent_exam_id', '=', self.talent_exam_id.id)])) > 1:
                raise ValidationError('Exam Attendees already exist..!')
            
    @api.one
    @api.constrains('nslate_item_ids', 'is_nslate_required')
    def _check_nslate(self):
        if not self.nslate_item_ids and self.is_nslate_required == 'yes':
            raise ValidationError('Please add Nslate Items..!')

    @api.one
    @api.constrains('form_no')
    def _check_form_no(self):
        if self.form_no:
            if len(self.search([('form_no', '=', self.form_no)])) > 1:
                raise ValidationError('Form No. already exist..!')

    @api.multi
    @api.depends('student_full_name', 'res_no')
    def name_get(self):
        result = []
        for adm in self:
            try:
                if adm.student_full_name and adm.res_no:
                    name = '(' + str(adm.res_no) + ') ' + str(adm.student_full_name)
                else:
                    name = adm.name
                result.append((adm.id, name))
            except:
                result.append((adm.name, name))
        return result

    @api.onchange('gender_option')
    def _onchange_gender_option(self):
        if self.gender_option:
            self.gender = self.gender_option

    image = fields.Binary(string="Logo", attachment=True)
    academic_year = fields.Many2one('academic.year', "Academic Year",
                                    default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    current_date = fields.Date(string='Date', default=lambda self: fields.Date.today())
    form_no = fields.Char(string='Form No', size=9)
    res_no = fields.Char(string='Reservation No', size=15)
    admission_no = fields.Char(string='Admission No', size=15)
    branch_id = fields.Many2one('operating.unit', string='For Reservation')
    branch_id_at = fields.Many2one('operating.unit', string='At Reservation')
    office_type_id = fields.Many2one('pappaya.office.type', related='branch_id.office_type_id', string="Office Type")
    course_id = fields.Many2one('pappaya.course', string='Course')
    group_id = fields.Many2one('pappaya.group', string='Group')
    batch_id = fields.Many2one('pappaya.batch', string='Batch')
    package = fields.Many2one('pappaya.package', string='Package')
    package_id = fields.Many2one('pappaya.course.package', string='Course Package')
    medium_id = fields.Many2one('pappaya.master', string='Medium')
    previous_course_id = fields.Many2one('pappaya.course', string='Course')
    previous_group_id = fields.Many2one('pappaya.group', string='Group')
    previous_batch_id = fields.Many2one('pappaya.batch', string='Batch')
    previous_package_id = fields.Many2one('pappaya.package', string='Package')
    previous_course_package_id = fields.Many2one('pappaya.course.package', string='Course Package')
    previous_medium_id = fields.Many2one('pappaya.master', string='Medium')
    residential_type_id = fields.Many2one('residential.type', 'Student Residential Type')
    pre_stage_id = fields.Many2one('pappaya.business.stage', 'Pre Stage', default=None)
    is_fee_created = fields.Boolean('Is Fee created?')
    virtual_acc_no = fields.Char('Virtual Acc No')

    """ need to remove  student type and student type option fields once residential type revamped"""

    student_type = fields.Selection([('day', 'Day'), ('hostel', 'Hostel'), ('semi_residential', 'Semi Residential')],
                                    string='Student Type')
    student_type_option = fields.Selection(
        [('day', 'Day'), ('hostel', 'Hostel'), ('semi_residential', 'Semi Residential')], string='Student Type')
    """ """

    show_student_type = fields.Boolean(string='Show Student Type')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    gender_option = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    show_gender_option = fields.Boolean(string='Show Gender Option')
    center_id = fields.Selection([('general', 'General')], default='general', string='Center')
    old_new = fields.Selection([('old', 'Old'), ('new', 'New')], default='new', string='Old/New')
    incl_excl = fields.Selection([('inclusive', 'Inclusive'), ('exclusive', 'Exclusive')], default='inclusive',
                                 string='Inc/Exclusive')
    course_fee = fields.Float(string='Course Fee')
    course_fee_tax = fields.Float(string='Course Fee Tax')
    res_amount = fields.Float(string='Res. Amount')
    res_comm_amount = fields.Float(string='Comitted Amount')
    is_correspondent_student = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no',
                                                string='Is Correspondence Student?')
    sponsor_type = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no', string='Is Sponsor Required?')
    sponsor_doc_updated = fields.Boolean(string='Is Sponsor Document Updated?')
    sponsor_ref = fields.Char(string='Sponsor Ref', size=40)
    sponsor_id = fields.Many2one('pappaya.sponsor', string='Sponsor Name')
    material_amt = fields.Float(string='Material Amount', compute='compute_material_amount')
    nslate_amount = fields.Float(string='Total Amount', compute='compute_nslate_amount')
    uniform_amount = fields.Float(string='Total Amount', compute='compute_uniform_amount')
    nslate_item_ids = fields.One2many('pappaya.nslate.item', 'admission_id', string='Nslate')
    uniform_set_ids = fields.One2many('admission.uniform', 'admission_id', string='Uniform Set')
    is_transport = fields.Boolean(string='Is Transport?')
    is_transport_required = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no',
                                             string='Is Transport Required?')
    is_nslate = fields.Boolean(related='branch_id.is_nslate', string='Is Nslate?')
    is_nslate_required = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no', string='Is Nslate Required?')
    is_exam_attended = fields.Selection([('yes', 'Yes'), ('no', 'No')], default='no', string='Talent Exam Attended?')
    talent_exam_id = fields.Many2one('pappaya.talent.exam', string='Exam Attendees')
    transport_slab_id = fields.Many2one('pappaya.transport.stop', string='Transport Slab')
    service_route_id = fields.Many2one('pappaya.transport.route', string='Service Route')
    transport_fixed_amt = fields.Float(string='Transport Fixed Amt')
    transport_tax_amt = fields.Float(string='Transport Tax Amt')

    sur_name = fields.Char(string='Sur Name', size=10)
    student_name = fields.Char(string='Name', size=30)
    name = fields.Char("", size=64)
    father_name = fields.Char("Father Name", size=30)
    father_email = fields.Char("Father Email", size=254)
    father_occupation_id = fields.Many2one('pappaya.master', string="Father Occupation")
    mother_name = fields.Char("Mother Name", size=30)
    mother_email = fields.Char("Mother Email", size=254)
    mother_occupation_id = fields.Many2one('pappaya.master', string="Mother Occupation")
    mobile_one = fields.Char(string='Father Mobile', size=10)
    mobile_two = fields.Char(string='Mother Mobile', size=10)
    dob = fields.Date(string='Date of Birth')
    college_school = fields.Char(string='College/School')

    street = fields.Char(size=30)
    street2 = fields.Char(size=30)
    zip = fields.Char('Zipcode', size=6)
    city_id = fields.Many2one('pappaya.city', string='City')
    district_id = fields.Many2one('state.district', string='District')
    mandal_id = fields.Many2one('pappaya.mandal.marketing', string='Mandal')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self.env.user.company_id.country_id)
    temp_street = fields.Char('Street', size=30)
    temp_street2 = fields.Char('Street 2', size=30)
    temp_zip = fields.Char('Zipcode', size=6)
    temp_city_id = fields.Many2one('pappaya.city', string='City')
    temp_district_id = fields.Many2one('state.district', string='District')
    temp_mandal_id = fields.Many2one('pappaya.mandal.marketing', string='Mandal')
    temp_state_id = fields.Many2one('res.country.state', string="State")
    temp_country_id = fields.Many2one('res.country', string="Country",
                                      default=lambda self: self.env.user.company_id.country_id)
    phone = fields.Char(size=15)
    mobile = fields.Char(string='Mobile', size=10)
    phone_residence = fields.Char(string='Residence Phone', size=11)
    phone_office = fields.Char(string='Office Phone', size=11)
    addr_program_type = fields.Selection([('lt', 'LT')], default='lt', string='Program Type')
    stage_id = fields.Many2one('pappaya.business.stage', 'Status', default=None)
    is_final_stage = fields.Boolean('Final Stage', default=False)
    is_student_created = fields.Boolean('Final Stage', default=False)
    cancel = fields.Boolean('Cancel', default=False)
    active = fields.Boolean('Active', default=True)
    is_fees_not_paid = fields.Boolean('Fees not paid', default=False)
    is_fees_refunded = fields.Boolean('Fees Refunded', default=False)
    enquiry_histroy_o2m = fields.One2many('pappaya.enq.workflow.history', 'enquiry_id', string='History')
    enq_grade_doc_o2m = fields.One2many('pappaya.enq.grade_doc', 'enquiry_id', 'Grade Joining Document')
    student_full_name = fields.Char('Student Name', size=150)
    comm_place_holder = fields.Char('Locking Amount', size=64)
    update_fullname = fields.Boolean(compute='_get_student_fullname')
    student_address_id = fields.Many2one('pappaya.lead.stud.address', string="Lead Reference")
    aadhaar_no = fields.Char('Aadhaar No', size=12)
    aadhaar_file = fields.Binary('Aadhaar Upload')
    filename = fields.Char(string='Filename')
    hall_ticket_no = fields.Char('Hall Ticket No', size=20)
    board_type_id = fields.Many2one('pappaya.master', string="Board Type")
    board_code = fields.Char(string='Board Code', related='board_type_id.code', size=20)
    total_marks = fields.Float(string='Total Marks')
    rank = fields.Char(string='Rank', size=5)
    grade = fields.Char(string='Grade', size=5)
    type_of_admission = fields.Selection([('residential', 'Residential'), ('day_scholar', 'Day Scholar')],
                                         string='Type Of Admission')
    course_opted = fields.Selection(
        [('junior', 'Junior'), ('senior', 'Senior'), ('mpc', 'M.P.C'), ('bipc', 'Bi.P.C'), ('civils', 'CIVILS')],
        string='Course Opted')
    caste_id = fields.Many2one('pappaya.master', string="Caste")
    community_id = fields.Many2one('pappaya.master', string="Community")
    religion_id = fields.Many2one('pappaya.master', string="Religion")
    blood_group_id = fields.Many2one('pappaya.master', string="Blood Group")
    partner_id = fields.Many2one('res.partner', string="Student")
    total_invoiced_amount = fields.Monetary(compute='_get_total_invoiced', string="Total Invoiced")
    total_pending_amount = fields.Monetary(compute='_get_total_invoiced', string="Total Pending Amount ")
    currency_id = fields.Many2one('res.currency', string="Currency", help='Utility field to express amount currency',
                                  default=lambda self: self.env.user.company_id.currency_id, readonly=True)
    show_material = fields.Boolean()
    show_uniform = fields.Boolean()
    concession_percentage = fields.Float('Concession(%)')
    concession_type_id = fields.Many2one('pappaya.master', string="Concession Type")
    fees_collection_o2m_id = fields.One2many('student.fees.collection', 'enquiry_id', string='Fees Collection')
    material_set_ids = fields.Many2many('branchwise.material.line', string='Material Set')
    is_student_updated = fields.Boolean(string='Is Student Updated ?')
    is_soa_stage = fields.Boolean(string='Is SOA Stage?')
    application_no = fields.Char(string='Application No', size=20)
    is_adm_stage = fields.Boolean(string='Is Admission Stage?', default=False)
    is_res_stage = fields.Boolean(string='Is Reservation Stage?', default=False)
    is_two_yr_fee = fields.Boolean('Two Year Option', default=False)
    fees_opt_for = fields.Selection([('one_year', 'One Year'), ('two_year', 'Two Year'), ('three_year', 'Three Year')],
                                    string='Fees opt for', default='one_year')
    old_admission_no = fields.Char(string='Old Admission No')
    sponsor_value = fields.Selection([('full', 'Full Sponsor'), ('partial', 'Partial Sponsor')], string='Sponsor Type',
                                     default='full')
    sponsor_amt = fields.Float(string='Sponsor Amount')
    sponsor_pay_amt = fields.Float(string='Additional Amount')
    sponsor_paid = fields.Boolean(string='Sponsor Paid', default=False)

    
    # Marketing Details
    admission_from = fields.Selection([('cluster','Cluster'),('non_cluster','Non Cluster'),('direct','Direct')], 'Admission From', default='cluster')
    cluster_id = fields.Many2one('pappaya.cluster', 'Cluster')
    cluster_district_id = fields.Many2one('state.district', string='Cluster District')
    cluster_state_id = fields.Many2one('res.country.state', string='Cluster State')
    cluster_country_id = fields.Many2one('res.country', string='Cluster Country', default=lambda self: self.env.user.company_id.country_id)
    pro_staff = fields.Selection([('pro', 'PRO'), ('staff', 'Staff')], string='Employee Type', default='pro')
    staff_id = fields.Many2one('hr.employee', string='Staff Name', domain=[('id', '!=', 1)])
    principal_id = fields.Many2one('hr.employee', string='Principal Name', related='branch_id.principal_id')
    program_type = fields.Selection([('pre_admission', 'Pre Admission'), ('admission', 'Admission')], string='Program Type')
    
    @api.constrains('dob')
    def _check_dob(self):
        if self.dob:
            d1 = datetime.strptime(self.dob, "%Y-%m-%d").date()
            d2 = date.today()
            rd = relativedelta(d2, d1)
            age = str(rd.years) + ' years'
            if rd.years > 60:
                raise ValidationError('Age should not exceed more than 60 Years')

    @api.onchange('city_id')
    def _onchange_city(self):
        domain = []
        if self.city_id:
            city_obj = self.env['pappaya.city'].search([('id', '=', self.city_id.id)])
            for obj in city_obj:
                domain.append(obj.district_id.id)
            return {'domain': {'district_id': [('id', 'in', domain)]}}

    @api.onchange('temp_city_id')
    def _onchange_temp_city(self):
        t_domain = []
        if self.temp_city_id:
            temp_city_obj = self.env['pappaya.city'].search([('id', '=', self.temp_city_id.id)])
            for obj in temp_city_obj:
                t_domain.append(obj.district_id.id)
            return {'domain': {'temp_district_id': [('id', 'in', t_domain)]}}

    @api.onchange('district_id')
    def _onchange_district(self):
        domain = []
        if self.district_id:
            district_obj = self.env['state.district'].search([('id', '=', self.district_id.id)])
            for obj in district_obj:
                domain.append(obj.id)
            return {'domain': {'mandal_id': [('district_id', 'in', domain)]}}

    @api.onchange('temp_district_id')
    def _onchange_temp_district(self):
        t_domain = []
        if self.temp_district_id:
            t_district_obj = self.env['state.district'].search([('id', '=', self.temp_district_id.id)])
            for obj in t_district_obj:
                t_domain.append(obj.id)
            return {'domain': {'temp_mandal_id': [('district_id', 'in', t_domain)]}}

    @api.onchange('mandal_id')
    def _onchange_mandal(self):
        domain = []
        if self.mandal_id:
            mandal_obj = self.env['pappaya.mandal.marketing'].search([('id', '=', self.mandal_id.id)])
            for obj in mandal_obj:
                domain.append(obj.state_id.id)
            return {'domain': {'state_id': [('id', 'in', domain)]}}

    @api.onchange('temp_mandal_id')
    def _onchange_temp_mandal(self):
        t_domain = []
        if self.temp_mandal_id:
            temp_mandal_obj = self.env['pappaya.mandal.marketing'].search([('id', '=', self.temp_mandal_id.id)])
            for obj in temp_mandal_obj:
                t_domain.append(obj.state_id.id)
            return {'domain': {'temp_state_id': [('id', 'in', t_domain)]}}

    @api.one
    @api.constrains('concession_percentage')
    def check_valid_concession_percentage(self):
        if self.concession_percentage:
            if self.concession_percentage < 0.0 or self.concession_percentage > 100:
                raise ValidationError('Please enter the valid Percentage')

    @api.one
    @api.constrains('total_marks')
    def check_valid_total_marks(self):
        if self.total_marks:
            if self.total_marks < 0.0:
                raise ValidationError('Please enter the valid Total Marks')

    @api.multi
    def toggle_active(self):
        """ Inverse the value of the field ``active`` on the records in ``self``. """
        for record in self:
            if record.partner_id:
                record.partner_id.active = not record.active
            record.active = not record.active

    @api.multi
    def create_refund_fees(self):
        ret_fee_heads = []
        refund_fee = self.env['pappaya.fees.refund']
        fee_coll_srch = self.env['pappaya.fees.collection'].search([('enquiry_id', '=', self.id)])
        if self.stage_id.sequence <= 2:
            raise ValidationError('There is no Refundable Fees..!')
        if len(fee_coll_srch.ids) > 1:
            raise ValidationError('More than one Fee Collection is there in same academic year, \n'
                                  'Verify Admission and Fees Collection Records')

        if [s.id for s in fee_coll_srch.fees_collection_line if not s.name.is_soa_fee and s.term_state == 'processing']:
            raise ValidationError('The Payment is in Processing..!')

        if fee_coll_srch:
            refund_id = refund_fee.create({'student_id': self.partner_id.id if self.partner_id else None,
                                           'branch_id': self.branch_id_at.id,
                                           'admission_id': self.id,
                                           'course_package_id': self.package_id.id,
                                           'admission_no': self.admission_no if self.old_new == 'old' else self.res_no,
                                           'father_name': self.father_name,
                                           'fees_collection_id': fee_coll_srch.id,
                                           'is_update': True,
                                           'refund_type': 'reservation' if self.stage_id.sequence == 3 else 'admission',
                                           'refund_reason': 'Cancel - ' + str(self.stage_id.name)})

            for i in fee_coll_srch.fees_collection_line:
                if not i.name.is_soa_fee and not i.name.is_course_fee:
                    if not i.is_refunded and i.term_state == 'paid' and i.total_paid > 0:
                        ret_fee_heads.append((0, 0, {'fees_head_id': i.name.id,
                                                     'amount': i.amount,
                                                     'due_amount': i.due_amount,
                                                     'res_adj_amt': i.res_adj_amt,
                                                     'total_paid': i.total_paid,
                                                     'cgst': i.cgst,
                                                     'sgst': i.sgst,
                                                     'term_state': i.term_state,
                                                     'gst_total': i.gst_total}))

            if len(ret_fee_heads) > 0:
                refund_id.refund_line_ids = ret_fee_heads
            else:
                raise ValidationError('There is no Refundable Fees..!')
        else:
            raise ValidationError('There is no Fees Collection for this Student..!')
        self.is_fees_refunded = True

    @api.multi
    def cancel_stage_wiz(self):
        view_id = self.env['pappaya.enquiry.confirm.wizard']
        # value = self.get_wizard_value()
        new = view_id.create({})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirmation - Cancel Stage',
            'res_model': 'pappaya.enquiry.confirm.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': new.id,
            'view_id': self.env.ref('pappaya_admission.pappaya_enquiry_cancel_stage_wizard', False).id,
            'target': 'new',
        }

    @api.multi
    def cancel_stage(self, description):
        fee_coll_srch = self.env['pappaya.fees.collection'].search([('enquiry_id', '=', self.id)])
        if len(fee_coll_srch.ids) > 1:
            raise ValidationError('More than one Fee Collection is there in same academic year, \n'
                                  'Verify Admission and Fees Collection Records')

        self.cancel = True
        fee_coll_srch.admission_cancel = True
        hist_obj = self.env['pappaya.enq.workflow.history']
        mov_cont = self.stage_id.name + ' Cancel'
        value = {
            'document_number': self.form_no or '',
            'movement_stage': mov_cont,
            'user_id': self.env.uid,
            'updated_on': datetime.today(),
            'enquiry_id': self.id,
            'description': description,
            'course_id': self.course_id.id,
            'group_id': self.group_id.id,
            'batch_id': self.batch_id.id,
            'package_id': self.package.id,
            'course_package_id': self.package_id.id,
            'medium_id': self.medium_id.id,
        }
        hist_obj.create(value)

    @api.multi
    def admission_reactivate(self):
        """ Admission Reactivated once cancel is happened but fees not refunded """
        fee_coll_srch = self.env['pappaya.fees.collection'].search([('enquiry_id', '=', self.id)])
        if len(fee_coll_srch.ids) > 1:
            raise ValidationError('More than one Fee Collection is there in same academic year, \n'
                                  'Verify Admission and Fees Collection Records')

        self.cancel = False
        fee_coll_srch.admission_cancel = False

        # refund_fee = self.env['pappaya.fees.refund']
        # adm_no = self.admission_no if self.old_new == 'old' else self.res_no
        # refund_srch = refund_fee.search([('admission_no','=',adm_no),
        #                                  ('academic_year_id','=',self.academic_year.id)])
        # if refund_srch:
        #     if refund_srch[0].state in ['draft','requested','rejected']:
        #         refund_srch[0].fees_collection_id.admission_cancel = False
        #         refund_srch[0].state = 'rejected'
        #         refund_srch[0].refund_reason = str(refund_srch[0].refund_reason) + ' Reactivated Again'
        #         self.cancel = False
        #     else:
        #         raise ValidationError('You cannot reactivate-Refund process completed')

    @api.multi
    def _get_total_invoiced(self):
        for record in self:
            total_invoiced_amount = 0.0;
            total_pending_amount = 0.0
            for inv_obj in self.env['account.invoice'].search([('admission_id', '=', record.id)]):
                for ai_paid in self.env['account.payment'].search([('invoice_ids', 'in', inv_obj.id)]):
                    total_invoiced_amount += ai_paid.amount
            record.total_invoiced_amount = total_invoiced_amount
            for ai_pending in self.env['account.invoice'].search(
                    [('admission_id', '=', record.id), ('state', 'in', ['draft', 'open'])]):
                total_pending_amount += ai_pending.residual
            record.total_pending_amount = total_pending_amount

    # For Invoice smart button
    @api.multi
    def action_admission_bills(self):
        self.ensure_one()
        tree_view_id = self.env.ref('account.invoice_tree').id
        form_view_id = self.env.ref('account.invoice_form').id
        form_search_id = self.env.ref('account.view_account_invoice_filter').id
        invoice_domain = [('admission_id', '=', self.id)]
        admission_bill_state = self._context.get('admission_bill_state')
        if admission_bill_state == 'paid':
            invoice_domain.append(('state', '=', 'paid'))
        elif admission_bill_state == 'pending':
            invoice_domain.append(('state', 'in', ['draft', 'open']))
        return {
            'name': _('Student Bills'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [[tree_view_id, 'tree'], [form_view_id, 'form'], [form_search_id, 'search']],
            'target': 'current',
            'res_model': 'account.invoice',
            'domain': invoice_domain,
        }

    @api.depends('nslate_item_ids.price_subtotal')
    def compute_nslate_amount(self):
        for record in self:
            amount = 0.0
            for item in record.nslate_item_ids:
                amount += item.price_subtotal
            record.nslate_amount = amount

    @api.depends('uniform_set_ids.price_subtotal')
    def compute_uniform_amount(self):
        for record in self:
            amount = 0.0
            for item in record.uniform_set_ids:
                amount += item.price_subtotal
            record.uniform_amount = amount

    @api.depends('material_set_ids.price_subtotal')
    def compute_material_amount(self):
        for record in self:
            amount = 0.0
            for item in record.material_set_ids:
                amount += item.price_subtotal
            record.material_amt = amount

    @api.onchange('talent_exam_id')
    def _onchange_talent_exam_id(self):
        if self.talent_exam_id:
            self.sur_name = self.talent_exam_id.sur_name
            self.name = self.talent_exam_id.name
            self.branch_id = self.talent_exam_id.school_id.id
            self.branch_id_at = self.talent_exam_id.school_id.id
            self.gender = self.talent_exam_id.gender
            self.gender_option = self.talent_exam_id.gender
            self.father_name = self.talent_exam_id.father_name
            self.father_email = self.talent_exam_id.father_email
            self.mother_email = self.talent_exam_id.mother_email
            self.mother_name = self.talent_exam_id.mother_name
            self.mobile_one = self.talent_exam_id.father_mobile
            self.mobile_two = self.talent_exam_id.mother_mobile
            self.dob = self.talent_exam_id.dob
            self.street = self.talent_exam_id.street
            self.temp_street = self.talent_exam_id.street
            self.temp_zip = self.talent_exam_id.zip
            self.zip = self.talent_exam_id.zip
            self.blood_group_id = self.talent_exam_id.blood_group_id.id
            self.city_id = self.talent_exam_id.city_id.id
            self.temp_city_id = self.talent_exam_id.city_id.id
            self.caste_id = self.talent_exam_id.caste_id.id
            self.state_id = self.talent_exam_id.state_id.id
            self.temp_state_id = self.talent_exam_id.state_id.id
            self.country_id = self.talent_exam_id.country_id.id

    @api.onchange('branch_id_at')
    def onchange_branch_id_at(self):
        domain = {}
        if self.branch_id_at:
            branch_ids = self.env['operating.unit'].sudo().search(
                [('parent_id', '=', self.branch_id_at.parent_id.id)]).ids
            self.branch_id = self.branch_id_at.id
            return {'domain': {'branch_id': [('id', 'in', branch_ids)]}}

    @api.onchange('branch_id', 'residential_type_id')
    def onchange_branch_id(self):
        if self.branch_id.is_transport and self.residential_type_id and self.residential_type_id.code != 'hostel':
            self.is_transport = True
        else:
            self.is_transport = False

    @api.onchange('academic_year', 'branch_id')
    def onchange_academic_year(self):
        course_domain = []
        branch_ids = self.env['operating.unit'].sudo().search([]).ids
        if self.academic_year and self.branch_id:
            self.course_id = None
            self.group_id = None
            self.batch_id = None
            self.package = None
            self.package_id = None
            branch_ids = self.env['operating.unit'].sudo().search(
                [('parent_id', '=', self.branch_id.parent_id.id)]).ids
            if self.branch_id.gender == 'boys':
                self.gender = 'male';
                self.gender_option = 'male'
            if self.branch_id.gender == 'girls':
                self.gender = 'female';
                self.gender_option = 'female'
            if self.branch_id.gender == 'co_education':
                self.show_gender_option = True

            if len(self.branch_id.residential_type_ids.ids) == 1:
                self.residential_type_id = self.branch_id.residential_type_ids.ids[0]
            else:
                self.show_student_type = True

            for academic in self.branch_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year.id:
                    for course_package in academic.course_package_ids:
                        course_domain.append(course_package.course_id.id)
        ##### Check couching center to pay 2 year options #############
        if self.branch_id.office_type_id.type == 'coaching':
            self.is_two_yr_fee = True
        else:
            self.is_two_yr_fee = False
        #######################################
        return {'domain': {'course_id': [('id', 'in', course_domain)],
                           'branch_id_at': [('id', 'in', branch_ids)]}}

    @api.onchange('course_id')
    def onchange_course_id(self):
        domain = []
        if self.academic_year and self.branch_id:
            self.group_id = None;
            self.batch_id = None;
            self.package = None;
            self.package_id = None
            for academic in self.branch_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id:
                            domain.append(course_package.group_id.id)
        return {'domain': {'group_id': [('id', 'in', domain)]}}

    @api.onchange('group_id')
    def onchange_group_id(self):
        domain = []
        if self.academic_year and self.branch_id:
            self.batch_id = None;
            self.package = None;
            self.package_id = None
            for academic in self.branch_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id:
                            domain.append(course_package.batch_id.id)
        return {'domain': {'batch_id': [('id', 'in', domain)]}}

    @api.onchange('batch_id')
    def onchange_batch_id(self):
        domain = []
        if self.academic_year and self.branch_id:
            self.package = None;
            self.package_id = None
            for academic in self.branch_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id and course_package.batch_id.id == self.batch_id.id:
                            domain.append(course_package.package_id.id)
        return {'domain': {'package': [('id', 'in', domain)]}}

    @api.onchange('package')
    def onchange_package(self):
        domain = []
        if self.academic_year and self.branch_id:
            self.package_id = None
            for academic in self.branch_id.course_config_ids:
                if academic.academic_year_id.id == self.academic_year.id:
                    for course_package in academic.course_package_ids:
                        if course_package.course_id.id == self.course_id.id and course_package.group_id.id == self.group_id.id and course_package.batch_id.id == self.batch_id.id and course_package.package_id.id == self.package.id:
                            domain.append(course_package.id)

        if self.academic_year and self.branch_id and self.course_id and self.group_id and self.batch_id and self.package:
            fees_struct = self.env['pappaya.fees.structure'].search([('academic_year_id', '=', self.academic_year.id),
                                                                     ('school_id', '=', self.branch_id.id),
                                                                     ('course_id', '=', self.course_id.id),
                                                                     ('group_id', '=', self.group_id.id),
                                                                     ('batch_id', '=', self.batch_id.id),
                                                                     ('package_id', '=', self.package.id),
                                                                     ('residential_type_id', '=',
                                                                      self.residential_type_id.id),
                                                                     ('type', '=', self.course_id.type)])
            com_amount = 0.0
            for f in fees_struct.structure_line_ids:
                if f.fees_id.is_course_fee:
                    com_amount = f.v_amount if self.old_new == 'old' else f.new_total
                    self.comm_place_holder = " Course Amount is Rs. %s" % str("{0:,.2f}".format(com_amount))
        return {'domain': {'package_id': [('id', 'in', domain)]}}

    @api.onchange('package_id')
    def onchange_package_id(self):
        if self.package_id:
            show_material = False
            show_uniform = False
            domain = [('academic_year_id', '=', self.academic_year.id), ('school_id', '=', self.branch_id.id),
                      ('course_id', '=', self.course_id.id),
                      ('group_id', '=', self.group_id.id if self.group_id.id else False),
                      ('batch_id', '=', self.batch_id.id if self.batch_id.id else False),
                      ('residential_type_id', '=', self.residential_type_id.id if self.residential_type_id else False),
                      ('type', '=', self.course_id.type if self.course_id else False),
                      ('package_id', '=', self.package.id if self.package else False)]
            for fees_struct in self.env['pappaya.fees.structure'].search(domain):
                for fs in fees_struct.structure_line_ids:
                    if fs.fees_id.is_material_fee:
                        show_material = True
                    if fs.fees_id.is_uniform_fee:
                        show_uniform = True
                self.show_uniform = show_uniform
                self.show_material = show_material
            return {'domain': {'medium_id': [('type', '=', 'medium'), ('id', 'in', self.branch_id.medium_ids.ids)]}}

    @api.onchange('student_address_id')
    def _onchange_student_address_id(self):
        if self.student_address_id:
            self.name = self.student_address_id.name
            self.father_name = self.student_address_id.father_name
            self.previous_course = self.student_address_id.studying_course_id.name
            self.mobile_one = self.student_address_id.mobile
            self.temp_country_id = self.country_id = self.student_address_id.state_id.country_id.id
            self.district_id = self.temp_district_id = self.student_address_id.district_id.id
            self.state_id = self.temp_state_id = self.student_address_id.state_id.id
            self.zip = self.temp_zip = self.student_address_id.pincode
            self.staff_id = self.student_address_id.employee_id.id

    @api.onchange('staff_id')
    def onchange_staff_id(self):
        if self.staff_id.staff_type not in ['pro', 'proadmin']:
            self.pro_staff = 'staff'

    @api.onchange('emp_id')
    def onchange_emp_id(self):
        if self.emp_id:
            emp = self.env['hr.employee'].search([('emp_id', '=', str(self.emp_id).strip()), ('active', '=', True)],
                                                 limit=1)
            if emp:
                self.staff_id = emp.id
                if emp.staff_type not in ['pro', 'proadmin']:
                    self.pro_staff = 'staff'
            else:
                raise ValidationError('Please enter the valid Employee ID')

    @api.multi
    def _get_student_fullname(self):
        for record in self:
            student_full_name = ''
            if record.name and not record.sur_name:
                student_full_name = str(record.name)
            elif record.sur_name and record.name:
                student_full_name = str(record.sur_name) + ' ' + str(record.name)
            record.student_full_name = student_full_name
            record.write({'student_full_name': student_full_name})

    @api.onchange('sur_name', 'name')
    def _onchange_first_name(self):
        student_full_name = ''
        if self.name and not self.sur_name:
            student_full_name = str(self.name)
        elif self.sur_name and self.name:
            student_full_name = str(self.sur_name) + ' ' + str(self.name)
        self.student_full_name = student_full_name

    @api.onchange('is_transport_required')
    def _onchange_is_transport_required(self):
        if self.is_transport_required:
            self.transport_slab_id = self.service_route_id = None

    @api.onchange('service_route_id')
    def _onchange_service_route_id(self):
        if self.service_route_id:
            self.transport_slab_id = None

    @api.onchange('is_nslate_required')
    def _onchange_is_nslate_required(self):
        if self.is_nslate_required:
            self.nslate_item_ids = None

    @api.onchange('is_exam_attended')
    def _onchange_is_exam_attended(self):
        if self.is_exam_attended:
            self.talent_exam_id = None

    @api.onchange('sponsor_type')
    def _onchange_sponsor_type(self):
        if self.sponsor_type:
            self.sponsor_id = None
        if self.sponsor_type == 'yes':
            fees_struct = self.env['pappaya.fees.structure'].search([('academic_year_id', '=', self.academic_year.id),
                                                                     ('school_id', '=', self.branch_id.id),
                                                                     ('course_id', '=', self.course_id.id),
                                                                     ('group_id', '=', self.group_id.id),
                                                                     ('batch_id', '=', self.batch_id.id),
                                                                     ('package_id', '=', self.package.id),
                                                                     ('residential_type_id', '=', self.residential_type_id.id),
                                                                     ('type', '=', self.course_id.type)])
            com_amount = 0.0
            for f in fees_struct.structure_line_ids:
                if f.fees_id.is_course_fee:
                    com_amount = f.v_amount if self.old_new == 'old' else f.new_total
            self.res_comm_amount = com_amount

    @api.onchange('dob')
    def _onchange_dob(self):
        if self.dob:
            today = date.today();
            value = datetime.strptime(self.dob, "%Y-%m-%d").date()
            if value > today:
                raise ValidationError("'Date of Birth' should not be current or future date.")

    @api.onchange('rank')
    def _onchange_rank(self):
        if self.rank:
            if not re.match('^[\d]*$', self.rank):
                raise ValidationError("Rank should be should not be less than zero.")

    @api.onchange('aadhaar_no')
    def _onchange_aadhaar_no(self):
        if self.aadhaar_no:
            self.env['res.company'].validation_student_aadhaar_no(self.aadhaar_no)

    @api.onchange('mobile_one')
    def onchange_mobile_one(self):
        if self.mobile_one:
            self.env['res.company'].validate_mobile(self.mobile_one)

    @api.onchange('mobile_two')
    def onchange_mobile_two(self):
        if self.mobile_two:
            self.env['res.company'].validate_mobile(self.mobile_two)

    @api.onchange('father_email')
    def onchange_father_email(self):
        if self.father_email:
            self.env['res.company'].validate_email(self.father_email)

    @api.onchange('mother_email')
    def onchange_mother_email(self):
        if self.mother_email:
            self.env['res.company'].validate_email(self.mother_email)

    @api.onchange('old_new')
    def onchange_old_new(self):
        if self.academic_year and self.branch_id and self.course_id and self.group_id and self.batch_id and self.package:
            fees_struct = self.env['pappaya.fees.structure'].search([('academic_year_id', '=', self.academic_year.id),
                                                                     ('school_id', '=', self.branch_id.id),
                                                                     ('course_id', '=', self.course_id.id),
                                                                     ('group_id', '=', self.group_id.id),
                                                                     ('batch_id', '=', self.batch_id.id),
                                                                     ('package_id', '=', self.package.id),
                                                                     ('residential_type_id', '=',
                                                                      self.residential_type_id.id),
                                                                     ('type', '=', self.course_id.type)])
            com_amount = 0.0
            for f in fees_struct.structure_line_ids:
                if f.fees_id.is_course_fee:
                    com_amount = f.v_amount if self.old_new == 'old' else f.new_total
                    self.comm_place_holder = " Course Amount is Rs. %s" % str("{0:,.2f}".format(com_amount))

    def validate_residence_phone(self, phone_no):
        if phone_no:
            match_phone_no = re.match('^[\d]*$', phone_no)
            if not match_phone_no or len(phone_no) < 11:
                raise ValidationError('Please enter a valid Residence Phone No.')
            return True
        else:
            return False

    def validate_office_phone(self, phone_no):
        if phone_no:
            match_phone_no = re.match('^[\d]*$', phone_no)
            if not match_phone_no or len(phone_no) < 11:
                raise ValidationError('Please enter a valid Office Phone No.')
            return True
        else:
            return False

    def _validate_vals(self, vals):
        if 'dob' in vals.keys() and vals.get('dob'):
            today = date.today();
            value = datetime.strptime(vals.get('dob'), "%Y-%m-%d").date()
            if value >= today:
                raise ValidationError("'Date of Birth' should not be current or future date.")
        if 'rank' in vals.keys() and vals.get('rank'):
            if not re.match('^[\d]*$', vals.get('rank')):
                raise ValidationError("Rank should be numbers.")
        if 'mobile_one' in vals.keys() and vals.get('mobile_one'):
            self.env['res.company'].validate_mobile(vals.get('mobile_one'))
        if 'admission_no' in vals.keys() and vals.get('admission_no'):
            vals['res_no'] = vals.get('admission_no')
        if 'mobile_two' in vals.keys() and vals.get('mobile_two'):
            self.env['res.company'].validate_mobile(vals.get('mobile_two'))
        if 'father_email' in vals.keys() and vals.get('father_email'):
            self.env['res.company'].validate_email(vals.get('father_email'))
        if 'mother_email' in vals.keys() and vals.get('mother_email'):
            self.env['res.company'].validate_email(vals.get('mother_email'))
        if 'phone_residence' in vals.keys() and vals.get('phone_residence'):
            self.validate_residence_phone(vals.get('phone_residence'))
        if 'phone_office' in vals.keys() and vals.get('phone_office'):
            self.validate_office_phone(vals.get('phone_office'))
        if 'zip' in vals.keys() and vals.get('zip'):
            self.env['res.company'].validate_zip(vals.get('zip'))
        if 'temp_zip' in vals.keys() and vals.get('temp_zip'):
            self.env['res.company'].validate_zip(vals.get('temp_zip'))
        if 'aadhaar_no' in vals.keys() and vals.get('aadhaar_no'):
            self.env['res.company'].validation_student_aadhaar_no(vals.get('aadhaar_no'))
        return vals

    @api.model
    def create(self, vals):
        self._validate_vals(vals)
        branch_id = vals.get('branch_id')
        com_obj = self.env['operating.unit'].browse(branch_id)

        if com_obj.gender != 'co_education':
            vals.update({'gender': 'female' if com_obj.gender == 'girls' else 'male'})
            vals.update({'gender_option': 'female' if com_obj.gender == 'girls' else 'male'})
        else:
            vals.update({'gender': vals.get('gender_option')})

        if 'academic_year' in vals and 'branch_id' in vals and 'course_id' in vals \
                and 'group_id' in vals and 'batch_id' in vals and 'package' in vals and 'old_new' in vals:
            fees_struct = self.env['pappaya.fees.structure'].search([('academic_year_id', '=', vals['academic_year']),
                                                                     ('school_id', '=', vals['branch_id']),
                                                                     ('course_id', '=', vals['course_id']),
                                                                     ('group_id', '=', vals['group_id']),
                                                                     ('batch_id', '=', vals['batch_id']),
                                                                     ('package_id', '=', vals['package']),
                                                                     ('residential_type_id', '=',
                                                                      vals['residential_type_id']),
                                                                     ('type', '=', self.env['pappaya.course'].search(
                                                                         [('id', '=', vals['course_id'])]).type if vals[
                                                                         'course_id'] else None)])
            com_amount = 0.0
            for f in fees_struct.structure_line_ids:
                if f.fees_id.is_course_fee:
                    com_amount = f.v_amount if self.old_new == 'old' else f.new_total
                    vals['comm_place_holder'] = "Course Amount is Rs. %s" % str("{0:,.2f}".format(com_amount))
        return super(PappayaAdmission, self).create(vals)

    @api.multi
    def write(self, vals):
        self._validate_vals(vals)
        ay = vals['academic_year'] if 'academic_year' in vals else self.academic_year.id
        branch = vals['branch_id'] if 'branch_id' in vals else self.branch_id.id
        course = vals['course_id'] if 'course_id' in vals else self.course_id.id
        group = vals['group_id'] if 'group_id' in vals else self.group_id.id
        batch = vals['batch_id'] if 'batch_id' in vals else self.batch_id.id
        package = vals['package'] if 'package' in vals else self.package.id
        old_new = vals['old_new'] if 'old_new' in vals else self.old_new
        residential_type_id = vals[
            'residential_type_id'] if 'residential_type_id' in vals else self.residential_type_id.id

        fees_struct = self.env['pappaya.fees.structure'].search([('academic_year_id', '=', ay),
                                                                 ('school_id', '=', branch),
                                                                 ('course_id', '=', course),
                                                                 ('group_id', '=', group),
                                                                 ('batch_id', '=', batch),
                                                                 ('residential_type_id', '=', residential_type_id),
                                                                 ('type', '=', self.env['pappaya.course'].search(
                                                                     [('id', '=', course)]).type),
                                                                 ('package_id', '=', package)], limit=1)
        com_amount = 0.0
        for f in fees_struct.structure_line_ids:
            if f.fees_id.is_course_fee:
                com_amount = f.v_amount if old_new == 'old' else f.new_total
                vals['comm_place_holder'] = "Course Amount is Rs. %s" % str("{0:,.2f}".format(com_amount))

        return super(PappayaAdmission, self).write(vals)

    @api.one
    @api.constrains('res_comm_amount', 'old_new')
    def check_commited_amount(self):
        if self.res_comm_amount <= 0.0 and self.sponsor_type == 'no':
            raise ValidationError('Committed Amount should be greater than 0')

        fees_struct = self.env['pappaya.fees.structure'].search([('academic_year_id', '=', self.academic_year.id),
                                                                 ('school_id', '=', self.branch_id.id),
                                                                 ('course_id', '=', self.course_id.id),
                                                                 ('group_id', '=', self.group_id.id),
                                                                 ('batch_id', '=', self.batch_id.id),
                                                                 ('residential_type_id', '=',
                                                                  self.residential_type_id.id),
                                                                 ('package_id', '=', self.package.id)], limit=1)
        lock_in_amount = 0.0
        actual_amount = 0.0
        for marketing_slab in fees_struct.lock_in_fee_slab_ids:
            if marketing_slab.is_active:
                lock_in_amount = marketing_slab.locked_amount_new if self.old_new == 'new' else marketing_slab.locked_amount_old
                break
        for f in fees_struct.structure_line_ids:
            if f.fees_id.is_course_fee:
                actual_amount = f.amount if self.old_new == 'old' else f.new_total

        if lock_in_amount == 0.0 and self.sponsor_type == 'no':
            raise ValidationError('Please configure Lock-In Amount in Course Fees (Fees Structure)')

        if not lock_in_amount <= self.res_comm_amount <= actual_amount and self.sponsor_type == 'no':
            raise ValidationError(
                'Committed Amount should be between the configured Lock-In Amount (%s) and Actual Amount (%s)' % (
                    str("{0:,.2f}".format(lock_in_amount)), str("{0:,.2f}".format(actual_amount))))
            # raise ValidationError('Comitted Amount should be greater then configured Lock-In Amount ')

    @api.one
    @api.constrains('residential_type_id')
    def check_student_type(self):
        if self.residential_type_id.id not in self.branch_id.residential_type_ids.ids:
            raise ValidationError('Chosen Student Residential type not availabale for this Branch.')

    @api.multi
    def create_sale_invoice(self):
        # Creating partner record
        receivable_coa_account = self.env['account.account'].search(
            [('user_type_id', '=', self.env.ref('account.data_account_type_receivable').id),
             ('company_id', '=', self.env.user.company_id.id)], limit=1)
        #         income_coa_account = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_other_income').id),
        #                                                               ('company_id','=',self.branch_id_at.id)], limit=1)
        if self.partner_id:
            partner_obj = self.partner_id
        else:
            partner_obj = self.env['res.partner'].create({'name': (self.form_no or '') + ' (' + self.name + ')',
                                                          'is_company': False,
                                                          'customer': True,
                                                          'company_type': 'person',
                                                          'status': 'new',
                                                          'type': 'invoice',
                                                          'admission_academic_year_id': self.academic_year.id,
                                                          #                                                           'property_account_receivable_id':  income_coa_account.id,
                                                          'school_id': self.branch_id_at.id,
                                                          'company_id': self.env.user.company_id.id
                                                          })
            self.partner_id = partner_obj.id

        # Updating product list
        invoice_line_ids = []
        acc = self._default_journal()
        if not acc:
            raise ValidationError('Need to configure COA for selected company Journal.')
        journal = self._default_journal()
        #         account = self._default_journal().default_debit_account_id
        if not journal:
            raise ValidationError('Configure default account id in Journal')

        #         print('*****************************************************************************************************************************')
        #         print ('receivable_coa_account Name : ', receivable_coa_account.name)
        #         print ('receivable_coa_account Id : ', receivable_coa_account.id)
        #         print ('Journal Name: ', journal.name)
        #         print ('Journal ID: ', journal.id)
        #         print ('partner Name: ', partner_obj.name)
        #         print ('partner ID: ', partner_obj.id)
        #         print('*****************************************************************************************************************************')
        #         for mat in self.material_set_ids:
        #             invoice_line_ids.append((0, 0, {'product_id': mat.product_id.id,
        #                                             'name': mat.product_id.name,
        #                                             'quantity': mat.product_uom_qty,
        #                                             'price_unit': mat.price_unit,
        #                                             'uom_id': mat.product_uom.id,
        #                                             'price_subtotal': mat.price_subtotal,
        #                                             'account_id': receivable_coa_account.id}))

        invoice = self.env['account.invoice'].create({'partner_id': partner_obj.id,
                                                      'admission_id': self.id,
                                                      'company_id': self.env.user.company_id.id,
                                                      'type': 'in_invoice',
                                                      'academic_year_id': self.academic_year.id,
                                                      'account_id': receivable_coa_account.id,
                                                      'journal_id': journal.id,
                                                      'invoice_line_ids': invoice_line_ids})
        #         invoice_vals = {
        #             'admission_id': self.id,
        #             'academic_year_id': self.academic_year.id,
        #             'name': '',
        #             'type': 'in_invoice',
        #             'partner_id': partner_id,
        #             'invoice_line_ids': [(0, 0, {'name': serv_cost.name,
        #                                          'product_id': serv_cost.id,
        #                                          'quantity': 2,
        #                                          'uom_id': serv_cost.uom_id.id,
        #                                          'price_unit': serv_cost.standard_price,
        # #                                          'account_analytic_id': so.analytic_account_id.id,
        #                                          'account_id': account_income.id})],
        #             'account_id': account_payable.id,
        #             'journal_id': journal.id,
        #             'currency_id': company.currency_id.id,
        #         }
        #         inv = self.env['account.invoice'].create(invoice_vals)

        # sale_order = sale_quotation.action_confirm()
        print('********************************************************************************')
        print('invoice : ', invoice)
        print('********************************************************************************')
        return {
            'name': _('Creating Fees invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'view_id': self.env.ref('account.invoice_form').id,
            'type': 'ir.actions.act_window',
            'res_id': invoice.id,
        }

    # End

    @api.multi
    def conform_stage(self):
        """For old students check for pending fees amount"""     
        context = {}
        fee_collection_id = False
        total_pending_fee = 0.0
        for fee_collection in self.env['pappaya.fees.collection'].sudo().search(
                ['|',('admission_number', '=', self.admission_no),('admission_number','=',self.old_admission_no), ('admission_cancel', '=', False)]):
            if fee_collection and fee_collection.enquiry_id.admission_no and (fee_collection.enquiry_id.admission_no == self.admission_no or fee_collection.enquiry_id.admission_no == self.old_admission_no) \
                and fee_collection.bulk_term_state in ['due', 'processing']:
                fee_collection_id = fee_collection
                context.update({'admission_number': self.admission_no if self.admission_no else self.old_admission_no })
                break;

        if not fee_collection_id and self.hall_ticket_no:
            fee_collection_id = self.env['pappaya.fees.collection'].sudo().search(
                [('enquiry_id.hall_ticket_no', '=', self.hall_ticket_no)], limit=1)
        if fee_collection_id:
            context.update({'hall_ticket_number': self.hall_ticket_no})
            if fee_collection_id and fee_collection_id.enquiry_id.admission_no and (fee_collection_id.enquiry_id.admission_no == self.admission_no or fee_collection_id.enquiry_id.admission_no == self.old_admission_no) and \
                fee_collection_id.enquiry_id.hall_ticket_no:
                for fee_line in fee_collection_id.fees_collection_line:
                    if not fee_line.name.is_course_fee and not fee_line.name.is_reservation_fee:
                        if fee_line.term_state == 'due':
                            total_pending_fee += fee_line.due_amount
                        elif fee_line.term_state == 'processing':
                            total_pending_fee += fee_line.total_paid

                context.update({'fee_collection_id': fee_collection_id.id, 'total_pending_fee': total_pending_fee})
    
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'old.student.pending.fees.wizard',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'context': context,
                    'view_id': self.env.ref('pappaya_admission.view_old_student_pending_fees_wizard_form', False).id,
                    'target': 'new',
                }

        businesss_stage = self.env['pappaya.business.stage']
        current_stage = None

        grade_stage_avail = businesss_stage.search([('school_id', '=', self.branch_id.id)])
        f_package_avail = self.env['pappaya.fees.structure'].search([('academic_year_id', '=', self.academic_year.id),
                                                                     ('course_id', '=', self.course_id.id),
                                                                     ('group_id', '=', self.group_id.id),
                                                                     ('batch_id', '=', self.batch_id.id),
                                                                     ('school_id', '=', self.branch_id.id),
                                                                     ('residential_type_id', '=',
                                                                      self.residential_type_id.id),
                                                                     ('type', '=', self.course_id.type),
                                                                     ('package_id', '=', self.package.id)])

        if not f_package_avail:
            raise ValidationError('Fees Structure is not created for the Branch/Course/Group/Batch')

        if not grade_stage_avail:
            raise ValidationError('Chosen Course is not configured in the Admission Stage workflow')

        # Updating Caution Deposit and pocket money in Student Profile
        if self.partner_id:
            for fee in self.fees_collection_o2m_id:
                if fee.name.is_caution_deposit_fee and fee.term_state == 'paid':
                    self.partner_id.caution_deposit += (fee.amount)
                if fee.name.is_pocket_money and fee.term_state == 'paid':
                    self.partner_id.student_wallet_amount += (fee.amount)

        if self.stage_id.sequence > 2 and self.old_new == 'new':
            self.existing_old_student()
            self.is_student_created = True

        if self.stage_id.sequence == 2:
            self.is_res_stage = True

        if self.stage_id.sequence == 4:
            self.is_adm_stage = True
            self.is_res_stage = False

        if self.stage_id:
            if self.stage_id.is_final_stage:
                return True
            current_stage = self.stage_id
            next_seq = self.stage_id.sequence + 1
        else:
            if self.old_new == 'old':
                next_seq = 2
                self.is_soa_stage = True
            else:
                next_seq = 1
        stag_flag = False

        while not stag_flag:
            stage_avail = businesss_stage.search([('sequence', '=', next_seq), ('school_id', '=', self.branch_id.id)])
            if stage_avail.id:
                stag_flag = True
                #### Seq number generation and alter #######
                old_seq = self.name
                seq_alter = self.name.split('/')
                self.pre_stage_id = self.stage_id.id
                # if self.stage_id.sequence ==2:
                #     res_sequence_no = self.env['ir.sequence'].next_by_code('pappaya.admission.reservation') or _('New')
                #     self.res_no = res_sequence_no
                self.stage_id = stage_avail.id
                ######## Seq number End ##########

                #### tracking history creation #######33
                cont = current_stage.name if current_stage else 'Start'
                mov_cont = cont + '->' + stage_avail.name
                hist_obj = self.env['pappaya.enq.workflow.history']
                amt, hist_amt = 0.0, 0.0
                for stud_fee in self.fees_collection_o2m_id:
                    if not stud_fee.name.is_course_fee_component and stud_fee.term_state == 'paid':
                        amt += stud_fee.total_paid
                for hist in self.enquiry_histroy_o2m:
                    hist_amt += hist.amount
                value = {'document_number': self.form_no or '',
                         'movement_stage': mov_cont,
                         'user_id': self.env.uid,
                         'updated_on': datetime.today(),
                         'enquiry_id': self.id,
                         'description': (str(self.branch_id.name) + ' -> ' + str(self.branch_id_at.name)),
                         'course_id': self.course_id.id,
                         'group_id': self.group_id.id,
                         'batch_id': self.batch_id.id,
                         'package_id': self.package.id,
                         'course_package_id': self.package_id.id,
                         'medium_id': self.medium_id.id,
                         'amount': (amt - hist_amt)
                         }
                hist_obj.create(value)
                ######## END - tracing history ################

                ##########  Notificataion method called ###########
                # self.send_enq_notification()
                ############  END ##############3
                if self.stage_id and self.stage_id.is_fin_short_list_stage:
                    self.is_shortlisted_stage = True
                if self.stage_id and self.stage_id.is_fees_applicable:
                    self.is_fees_not_paid = True
                    # self.create_fees()
                if self.stage_id and self.stage_id.is_final_stage:
                    self.is_final_stage = True

                if not self.is_fee_created:
                    self.create_fees()
                    self.is_fee_created = True
                ###### Grade joining Document ################
                ###########check mandatory doc ##########
                for i in self.enq_grade_doc_o2m:
                    if i.required and not i.document_file:
                        raise ValidationError(_('Required %s Document not attached') % i.document_name)
                ############### end mandatory doc ########
                grade_doc_obj = self.env['pappaya.enq.grade_doc']
                if self.stage_id.grade_join_doc_o2m:
                    for i in self.stage_id.grade_join_doc_o2m:
                        grade_doc_obj.create({'document_name': i.document_name,
                                              'wrk_grade_id': i.id,
                                              'required': i.required,
                                              'stage_name': self.stage_id.name,
                                              'enquiry_id': self.id})
                ################# End GRade joining document ########

                # ################ START - Sponsor Document ############
                if self.sponsor_type == 'yes' and self.sponsor_id.sponsor_doc_ids and not self.sponsor_doc_updated:
                    for line in self.sponsor_id.sponsor_doc_ids:
                        grade_doc_obj.create({'document_name': line.document_name,
                                              'sponsor_id': self.sponsor_id.id,
                                              'required': line.required,
                                              'stage_name': self.stage_id.name,
                                              'enquiry_id': self.id})
                    self.sponsor_doc_updated = True

                # ################# END - Sponsor Document ###########
            else:
                next_seq += 1
        # self.sibling_add =True

    @api.multi
    def _get_minimum_admisison_mandatory_fees(self):
        collection_id = self.env['pappaya.fees.collection'].search(
            [('academic_year_id', '=', self.academic_year.id), ('enquiry_id', '=', self.id)])
        mandatory_fees = 0.0;
        minimum_admission_fee = 0.0
        for fee_line in collection_id.fees_collection_line:
            if fee_line.name.is_compulsory_fee:
                mandatory_fees += fee_line.amount
        # Minimum Attendance Percentage
        minimum_percentage = self.env['pappaya.branch.ay.course.config'].search(
            [('operating_unit_id', '=', self.branch_id.id),
             ('academic_year_id', '=', self.academic_year.id)], limit=1).reservation_min_percentage
        if self.res_comm_amount == 0.0 and self.sponsor_type == 'no':
            raise ValidationError('Please configure locking amount in Course Fees (Fees Structure)')
        minimum_admission_fee = (self.res_comm_amount * minimum_percentage) / 100
        return mandatory_fees, minimum_admission_fee

    @api.multi
    def action_confirm(self):
        ''' Author : Nivas M 
            Purpose: The following code will make admission fields readonly, except first three tabs field, if admission reached SOA stage.
        '''
        # Enquiry
        if self.stage_id.sequence == 1:
            self.is_soa_stage = True
            collection_id = self.env['pappaya.fees.collection'].search(
                [('academic_year_id', '=', self.academic_year.id), ('enquiry_id', '=', self.id)])
            for fee_line in collection_id.fees_collection_line:
                if fee_line.name.id in self.stage_id.fees_id.ids:
                    if fee_line.term_state == 'due':
                        mis_fee_name = fee_line.name.name + '   --   Rs. ' + str(fee_line.amount) + '\n'
                        raise ValidationError('Please Pay the following fees and proceed.\n\n %s' % mis_fee_name)
        # Sale of Application            
        elif self.stage_id.sequence == 2:
            collection_id = self.env['pappaya.fees.collection'].search(
                [('academic_year_id', '=', self.academic_year.id), ('enquiry_id', '=', self.id)])
            for fee_line in collection_id.fees_collection_line:
                if fee_line.name.id in self.stage_id.fees_id.ids:
                    if fee_line.term_state == 'due':
                        mis_fee_name = fee_line.name.name + '   --   Rs. ' + str(fee_line.amount) + '\n'
                        raise ValidationError('Please Pay the following fees and proceed.\n\n %s' % mis_fee_name)
        # Reservation
        elif self.stage_id.sequence == 3:
            mandatory_fees, minimum_admission_fee = self._get_minimum_admisison_mandatory_fees()
            total_fees_required = mandatory_fees + minimum_admission_fee
            collection_id = self.env['pappaya.fees.collection'].search(
                [('academic_year_id', '=', self.academic_year.id), ('enquiry_id', '=', self.id)])
            total_reservatoin_paid = 0.0
            for fee_line in collection_id.fees_collection_line:
                if fee_line.name.is_reservation_fee or fee_line.name.is_course_fee_component and not fee_line.name.is_course_fee:
                    total_reservatoin_paid += fee_line.total_paid + fee_line.res_adj_amt
            if not total_reservatoin_paid >= total_fees_required:
                mis_fee_name = 'Minimum admission amount and mandatory fees' + '   --   Rs. ' + str(
                    (total_fees_required)) \
                               + '\n' + 'You already Paid' + '   --   Rs. ' + str((total_reservatoin_paid)) + '\n' \
                                                                                                              'You need to pay' + '   --   Rs. ' + str(
                    (total_fees_required - total_reservatoin_paid)) + '\n'
                raise ValidationError('Please Pay the following fees and proceed.\n\n %s' % mis_fee_name)

            """ Reservation Adjustments """
            self.adjust_reservation_fees()
            collection_id._update_course_fee_paid_status()

        #         ''' End '''
        #         if self.stage_id.sequence == 3:
        #             self.check_min()
        #         ##### check fee paid or not ###########
        #         if self.is_fees_not_paid and self.stage_id.sequence != 3:
        #             mis_fee_details = self.env['student.fees.collection'].search([('term_state','=','due'),
        #                                                                               ('enquiry_id', '=', self.id)])
        #             if mis_fee_details:
        #                 for i in mis_fee_details:
        #                     if i.name.is_reservation_fee:
        #                         mis_fee_list = [i.name.name + '   --   Rs. ' + str(i.amount) + '\n']
        #                     elif not i.name.is_reservation_fee:
        #                         mis_fee_list = [i.name.name + '   --   Rs. ' + str(i.due_amount) + '\n']
        #
        #                 mis_fee_name = ''
        #                 for i in mis_fee_list:
        #                     mis_fee_name += i
        #                 raise ValidationError('Please Pay the following fees and proceed.\n\n %s' % mis_fee_name)

        ############ END Check Fee #################
        view_id = self.env['pappaya.enquiry.confirm.wizard']
        value = self.get_wizard_value()
        if value['remarks_1']:
            new = view_id.create(value)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Confirmation - Next Stage Process',
                'res_model': 'pappaya.enquiry.confirm.wizard',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': new.id,
                'view_id': self.env.ref('pappaya_admission.pappaya_enquiry_confirm_wizard', False).id,
                'target': 'new',
            }

        else:
            self.conform_stage()

    @api.multi
    def adjust_reservation_fees(self):
        """ Reservation Adjustment has to be done here, """
        reservation_adj_heads = []
        collection_id = self.env['pappaya.fees.collection'].search([('academic_year_id', '=', self.academic_year.id), ('enquiry_id', '=', self.id)])
        reservation_line = collection_id._get_reservation_line()
        reservation_fees = reservation_line.total_paid
        fees_receipt_line_dict = [];
        fees_receipt_line_ids = [];
        fee_ledger_line = [];
        fee_receipt_ledger_line = []
        mov_line_ids = []
        reserv_adj_amt_tot = 0.0
        journal_obj = self.env['account.journal'].search([('code', '=', 'NARFC')], limit=1)
        for fee_line in collection_id.fees_collection_line:
            if fee_line.term_state == 'due' and not fee_line.name.is_course_fee:
                if fee_line.due_amount <= reservation_fees:
                    reservation_adj_heads.append(fee_line.id)
                    reservation_fees -= fee_line.due_amount                    
                    fee_line.write({
                        'res_adj_amt': fee_line.due_amount,
                        'due_amount': 0.0,
                        'term_state': reservation_line.term_state
                    })
                    fees_receipt_line_dict.append({
                        'name': fee_line.name.id,
                        'amount': fee_line.amount,
                        'concession_amount': fee_line.concession_amount,
                        'concession_type_id': fee_line.concession_type_id,
                        'total_paid': 0.0,
                        'res_adj_amt': fee_line.res_adj_amt,
                        'cgst': fee_line.cgst,
                        'sgst': fee_line.sgst,
                        'without_gst_amt': fee_line.amount,
                    })

                    line_ids = self._get_move_lines_from_adj(collection_id.enquiry_id.partner_id, fee_line.name,
                                                                 fee_line.res_adj_amt, journal_obj, collection_id)
                    # account_move = self._create_move_entry_from_adj(journal_obj, collection_id.school_id, line_ids)
                    # account_move.post()
                    mov_line_ids = mov_line_ids+line_ids
                    reserv_adj_amt_tot = reserv_adj_amt_tot+fee_line.res_adj_amt
                    ### Accounting entries ########
                    # if args['pay_type'] == 'cash':
                    #     line_ids = collection_id._get_move_lines(collection_id.enquiry_id.partner_id, fee_line.name,
                    #                                              fee_line.res_adj_amt, journal_obj, collection_id.school_id)
                    #     account_move = collection_id._create_move_entry(journal_obj, collection_id.school_id, line_ids)
                    #     account_move.post()
                    # if args['pay_type'] == 'bank':
                    #     if self.branch_id == self.branch_id_at:
                    #         collection_id._create_acc_journal_entries(collection_id.enquiry_id.partner_id, fee_line.name,
                    #                                                   fee_line.res_adj_amt, journal_obj, collection_id,
                    #                                                   args['deposit_bank'])
                    #     else:
                    #         self.create_six_acc_journal_ent()
                    ##### End #########
                    if fee_line.name.is_caution_deposit_fee:
                        self.partner_id.caution_deposit += fee_line.res_adj_amt
                    if fee_line.name.is_pocket_money:
                        self.partner_id.student_wallet_amount += fee_line.res_adj_amt
                elif fee_line.due_amount > reservation_fees and not reservation_fees == 0.0:
                    reservation_adj_heads.append(fee_line.id)
                    fee_line.write({
                        'res_adj_amt': reservation_fees,
                        'due_amount': (fee_line.due_amount - reservation_fees),
                    })
                    fees_receipt_line_dict.append({
                        'name': fee_line.name.id,
                        'amount': fee_line.amount,
                        'concession_amount': fee_line.concession_amount,
                        'concession_type_id': fee_line.concession_type_id,
                        'total_paid': 0.0,
                        'res_adj_amt': fee_line.res_adj_amt,
                        'cgst': fee_line.cgst,
                        'sgst': fee_line.sgst,
                        'without_gst_amt': fee_line.amount,
                    })
                    reservation_fees = 0.0
                    line_ids = self._get_move_lines_from_adj(collection_id.enquiry_id.partner_id, fee_line.name,
                                                             fee_line.res_adj_amt, journal_obj, collection_id)
                    # account_move = self._create_move_entry_from_adj(journal_obj, collection_id.school_id, line_ids)
                    # account_move.post()
                    mov_line_ids = mov_line_ids + line_ids
                    reserv_adj_amt_tot = reserv_adj_amt_tot + fee_line.res_adj_amt
                    ###### Accounting entries #######
                    # if args['pay_type'] == 'cash':
                    #     line_ids = collection_id._get_move_lines(collection_id.enquiry_id.partner_id, fee_line.name,
                    #                                              fee_line.res_adj_amt, journal_obj, collection_id.school_id)
                    #     account_move = collection_id._create_move_entry(journal_obj, collection_id.school_id, line_ids)
                    #     account_move.post()
                    # if args['pay_type'] == 'bank':
                    #     if self.branch_id == self.branch_id_at:
                    #         collection_id._create_acc_journal_entries(collection_id.enquiry_id.partner_id, fee_line.name,
                    #                                                   fee_line.res_adj_amt, journal_obj, collection_id,
                    #                                                   args['deposit_bank'])
                    #     else:
                    #         self.create_six_acc_journal_ent()
                    #### END #########
                    if fee_line.name.is_caution_deposit_fee:
                        self.partner_id.caution_deposit += fee_line.res_adj_amt
                    if fee_line.name.is_pocket_money:
                        self.partner_id.student_wallet_amount += fee_line.res_adj_amt
        if reservation_fees > 0.00:
            for fee_line in collection_id.fees_collection_line:
                if fee_line.name.is_caution_deposit_fee:
                    reservation_adj_heads.append(fee_line.id)
                    fee_line.write({
                        'res_adj_amt': fee_line.res_adj_amt + reservation_fees,
                        'due_amount': 0.0,
                        'term_state': reservation_line.term_state
                    })
                    updated = False
                    for fees_receipt_line_dic in fees_receipt_line_dict:
                        if fees_receipt_line_dic['name'] == fee_line.name.id:
                            fees_receipt_line_dic.update({
                                'res_adj_amt': fees_receipt_line_dic['res_adj_amt'] + reservation_fees,
                            })
                            updated = True
                    if not updated:
                        fees_receipt_line_dict.append({
                            'name': fee_line.name.id,
                            'amount': fee_line.amount,
                            'concession_amount': fee_line.concession_amount,
                            'concession_type_id': fee_line.concession_type_id,
                            'total_paid': 0.0,
                            'res_adj_amt': fee_line.res_adj_amt,
                            'cgst': fee_line.cgst,
                            'sgst': fee_line.sgst,
                            'without_gst_amt': fee_line.amount,
                        })
                    line_ids = self._get_move_lines_from_adj(collection_id.enquiry_id.partner_id, fee_line.name,
                                                             reservation_fees, journal_obj, collection_id)
                    # account_move = self._create_move_entry_from_adj(journal_obj, collection_id.school_id, line_ids)
                    # account_move.post()
                    mov_line_ids = mov_line_ids + line_ids
                    reserv_adj_amt_tot = reserv_adj_amt_tot + fee_line.res_adj_amt
                    ####### Accounting Entries #######
                    # if args['pay_type'] == 'cash':
                    #     line_ids = collection_id._get_move_lines(collection_id.enquiry_id.partner_id, fee_line.name,
                    #                                              reservation_fees, journal_obj, collection_id.school_id)
                    #     account_move = collection_id._create_move_entry(journal_obj, collection_id.school_id, line_ids)
                    #     account_move.post()
                    # if args['pay_type'] == 'bank':
                    #     if self.branch_id == self.branch_id_at:
                    #         collection_id._create_acc_journal_entries(collection_id.enquiry_id.partner_id, fee_line.name,
                    #                                                   fee_line.res_adj_amt, journal_obj, collection_id,
                    #                                                   args['deposit_bank'])
                    #     else:
                    #         self.create_six_acc_journal_ent()
                    ####  End #####
                    self.partner_id.caution_deposit += reservation_fees
                    reservation_fees = 0.0

                # Fee Ledger Line
                fee_ledger_line.append((0, 0, {
                    'fee_line_id': fee_line.id,
                    'name': fee_line.name.name,
                    'credit': fee_line.amount,
                    'concession_amount': fee_line.concession_amount,
                    'concession_type_id': fee_line.concession_type_id.id,
                    'debit': fee_line.total_paid,
                    'res_adj_amt': fee_line.res_adj_amt,
                    'balance': fee_line.amount - fee_line.res_adj_amt - (
                            fee_line.total_paid + fee_line.concession_amount),
                }))

        ###### Accounting Entry ######
        debit_acc_id = self.env['pappaya.fees.head'].search([('is_reservation_fee', '=', True)]).debit_account_id
        mov_line_ids.append((0, 0, {
            'name': collection_id.enquiry_id.partner_id.name,
            'debit': reserv_adj_amt_tot,
            'credit': 0,
            'account_id': debit_acc_id.id,
            'date': str(datetime.today().date()),
            'partner_id': collection_id.enquiry_id.partner_id.id,
            'journal_id': journal_obj.id,
            'company_id': journal_obj.company_id.id,
            'currency_id': journal_obj.company_id.currency_id.id,  # currency id of narayana
            'date_maturity': str(datetime.today().date()),
            'operating_unit_id': collection_id.school_id.id,
            'fees_collection_id': collection_id.id,
            }))
        ##########
        account_move = self._create_move_entry_from_adj(journal_obj, collection_id.school_id, mov_line_ids)
        account_move.post()

        for receipt_line in fees_receipt_line_dict:
            fees_receipt_line_ids.append((0, 0, receipt_line))

        res_adj_pay_mode = self.env['pappaya.paymode'].sudo().search(
            [('name', '=', 'Res Adj'), '|', ('active', '=', True), ('active', '=', False)])
        if not res_adj_pay_mode:
            res_adj_pay_mode = self.env['pappaya.paymode'].create({'name': 'Res Adj', 'active': False})

        receipt = self.env['pappaya.fees.receipt'].sudo().create({
            'state': 'paid',
            'fee_collection_id': collection_id.id,
            'school_id': collection_id.school_id.id,
            'academic_year_id': collection_id.academic_year_id.id,
            'name': collection_id.enquiry_id.id,
            'payment_mode_id': res_adj_pay_mode.id,
            'cheque_dd': '',
            'bank_name': False,
            'remarks': 'Reservation Fees Adjusted Details',
            'receipt_date': str(date.today()),
            'fees_receipt_line': fees_receipt_line_ids,
            'receipt_status': 'cleared'
        })

        for fees_receipt_line in receipt.fees_receipt_line:
            fee_receipt_ledger_line.append((0, 0, {
                'fees_receipt_id': receipt.id,
                'name': receipt.receipt_no,
                'posting_date': receipt.receipt_date,
                'fees_head': fees_receipt_line.name.name,
                'transaction': receipt.remarks,
                'concession_amount': fees_receipt_line.concession_amount,
                'payment_mode_id': receipt.payment_mode_id.id,
                'amount': fees_receipt_line.total_paid,
                'res_adj_amt': fees_receipt_line.res_adj_amt,
            }))

            # Ledger Updations
        ledger_obj = self.env['pappaya.fees.ledger'].search([('fee_collection_id', '=', collection_id.id)])
        ledger_obj.fee_receipt_ledger_line = fee_receipt_ledger_line
        course_fee_adj = 0.0;
        course_fee_debit = 0.0;
        course_fee_bal = 0.0
        
        for receipt_line in receipt.fees_receipt_line:
            for line in ledger_obj.fee_ledger_line:
                if receipt_line.name.name == line.name:
                    if receipt_line.name.is_course_fee_component:
                        course_fee_adj += receipt_line.res_adj_amt
                        course_fee_debit += receipt_line.total_paid
                        course_fee_bal += line.balance - receipt_line.total_paid - receipt_line.res_adj_amt
                    line.res_adj_amt = receipt_line.res_adj_amt
                    line.debit += receipt_line.total_paid
                    line.balance = line.balance - receipt_line.total_paid - receipt_line.res_adj_amt
                # Updating Course fee
                if line.fee_line_id.name.is_course_fee:
                    line.res_adj_amt = course_fee_adj
                    line.debit += course_fee_debit
                    line.balance = course_fee_bal
        
        return True

    @api.multi
    def pay_fees(self):
        fee_coll_srch = self.env['pappaya.fees.collection'].search([('enquiry_id', '=', self.id)])
        if self.cancel:
            raise ValidationError('Sorry, The admission is cancelled..!')
        if fee_coll_srch:
            # fee_coll_srch.pay_amount = fee_coll_srch.pay_due_total
            return {
                'type': 'ir.actions.act_window',
                # 'name': 'Confirmation - Next Stage Process',
                'res_model': 'pappaya.fees.collection',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': fee_coll_srch.id,
                'view_id': self.env.ref('pappaya_fees.pappaya_fees_collection_form', False).id,
                'target': 'new',
            }

        # else:
        #     raise ValidationError('No Pending Bills found for current admission record.')

    def get_wizard_value(self):
        for order in self:
            ############### Value ###############
            businesss_stage = self.env['pappaya.business.stage']
            if self.stage_id:
                next_seq = self.stage_id.sequence + 1
            else:
                next_seq = 1
            stag_flag = False

            while not stag_flag:
                stage_avail = businesss_stage.search(
                    [('sequence', '=', next_seq), ('school_id', '=', self.branch_id.id), ])
                if stage_avail.id:
                    stag_flag = True
                else:
                    next_seq += 1
            fees = stage_avail.fees_id if stage_avail.is_fees_applicable else ''
            fees_name = ''
            for i in fees:
                fees_name = fees_name + i.name + ","
            #####################################
            # view_id = self.env['pappaya.enquiry.confirm.wizard']
            value = {'stage': stage_avail.name,
                     'remarks_1': fees_name,
                     'fees': True if fees_name else False,
                     'remarks_2': ''}
            return value

    def check_min(self):
        if self.res_comm_amount <= 0.0:
            raise ValidationError('Please Committed Amount and proceed')
        fees_struct = self.env['pappaya.fees.structure'].search([('academic_year_id', '=', self.academic_year.id),
                                                                 ('school_id', '=', self.branch_id.id),
                                                                 ('course_id', '=', self.course_id.id),
                                                                 ('group_id', '=', self.group_id.id),
                                                                 ('batch_id', '=', self.batch_id.id),
                                                                 ('residential_type_id', '=',
                                                                  self.residential_type_id.id),
                                                                 ('type', '=', self.course_id.type),
                                                                 ('package_id', '=', self.package.id)])
        com_amount = 0.0
        res_amount = 0.0
        act_amt = 0.0
        for f in fees_struct.structure_line_ids:
            if f.fees_id.is_reservation_fee:
                res_amount = f.amount
            if f.fees_id.is_course_fee:

                if self.old_new == 'old':
                    com_amount = f.v_amount
                    act_amt = f.min_amount
                else:
                    com_amount = f.new_total
                    act_amt = f.new_stud_min_amount
        if com_amount == 0.0 and self.sponsor_type == 'no':
            raise ValidationError('Please configure locking amount in Course Fees (Fees Structure)')

        if self.res_comm_amount > com_amount or self.res_comm_amount < act_amt:
            raise ValidationError(
                'Comitted Amount should be between the configured Lock-In Amount (%s) and Actual Amount (%s)' % (
                    act_amt, com_amount))

        mis_fee_details = self.env['student.fees.collection'].search([('term_state', '=', 'due'),
                                                                      ('enquiry_id', '=', self.id)])
        # unpaid_invoice = self.env['account.invoice'].search([('admission_id', '=', self.id), ('state', 'in', ['draft', 'open'])])
        percentage = 0.0
        for b in self.branch_id.course_config_ids:
            if b.academic_year_id.id == self.academic_year.id:
                percentage = b.reservation_min_percentage

        if percentage > 0:
            # for inv in unpaid_invoice:
            #     for inv_line in inv.invoice_line_ids:
            #         fees_head = self.env['pappaya.fees.head'].search([('product_id', '=', inv_line.product_id.id)])
            #         if fees_head.is_course_fee:
            #             original_paid = com_amount * percentage / 100
            #             actual_paid = inv_line.paid_amount + inv_line.adjusted_amount #inv.amount_total - inv.residual
            #             if actual_paid < original_paid:
            #                 paid = original_paid - actual_paid
            #                 raise ValidationError('Needs to pay remaining Rs. %s for Course Fee.'%paid)

            for fee in mis_fee_details:
                if fee.name.is_course_fee:
                    original_paid = com_amount * percentage / 100
                    if fee.name.is_course_fee:
                        actual_paid = fee.amount - fee.due_amount
                        if actual_paid < original_paid:
                            paid = original_paid - actual_paid
                            raise ValidationError('Needs to pay remaining Rs. %s for Course Fee.' % paid)
        else:
            raise ValidationError('Needs to configure minimum reservation amount in Branch')

    @api.multi
    def enroll_student(self):
        if self.is_fees_refunded:
            raise ValidationError('Sorry, Your fees Refunded..!')
        if self.stage_id.is_final_stage:
            # Transport History
            history = {
                'branch_id': self.branch_id.id,
                'transport_slab_id': self.transport_slab_id.id,
                'route_id': self.service_route_id.id,
                'academic_year_id': self.academic_year.id,
                'active': True
            }
            if self.residential_type_id.code != 'hostel' and self.is_transport_required == 'yes':
                self.partner_id.write({'transport_history_ids': [(0, 0, history)]})

        self.existing_old_student()
        self.is_student_updated = True

    @api.multi
    def existing_old_student(self):
        if self.old_new == 'new' and not self.old_admission_no:
            stud_obj = self.env['res.partner'].search([('id', '=', self.partner_id.id), ('active', '=', True)])
        elif self.old_new == 'new' and self.old_admission_no:
            stud_obj = self.env['res.partner'].search(
                [('user_type', '=', 'student'), ('admission_no', '=', self.old_admission_no), ('active', '=', True)])
        else:
            stud_obj = self.env['res.partner'].search(
                [('user_type', '=', 'student'), ('admission_no', '=', self.admission_no), ('active', '=', True)])
        vals = {}
        vals['partner_id'] = stud_obj.id
        vals['user_type'] = 'student'
        vals['image'] = self.image
        vals['admission_id'] = self.id
        vals['form_no'] = self.form_no
        vals['admission_no'] = self.res_no
        # Student Details
        vals['student_full_name'] = self.student_full_name
        vals['sur_name'] = self.sur_name
        vals['name'] = self.name
        vals['date_of_birth'] = self.dob
        vals['date_of_joining'] = datetime.today().date()
        vals['gender'] = self.gender
        vals['aadhaar_no'] = self.aadhaar_no
        vals['aadhaar_file'] = self.aadhaar_file
        vals['filename'] = self.filename
        vals['blood_group_id'] = self.blood_group_id.id
        vals['religion_id'] = self.religion_id.id
        vals['caste_id'] = self.caste_id.id
        vals['community_id'] = self.community_id.id
        # Hall Ticket Info
        vals['hall_ticket_no'] = self.hall_ticket_no
        vals['board_type_id'] = self.board_type_id.id
        vals['board_code'] = self.board_code
        vals['course_opted'] = self.course_opted
        vals['total_marks'] = self.total_marks
        vals['rank'] = self.rank
        vals['grade'] = self.grade
        # Education Info
        vals['school_id'] = self.branch_id.id
        vals['course_id'] = self.course_id.id
        vals['group_id'] = self.group_id.id
        vals['batch_id'] = self.batch_id.id
        vals['package_id'] = self.package.id
        vals['course_package_id'] = self.package_id.id
        vals['medium_id'] = self.medium_id.id
        vals['previous_course_id'] = self.previous_course_id.id if self.previous_course_id else []
        vals['previous_group_id'] = self.previous_group_id.id if self.previous_group_id else []
        vals['previous_batch_id'] = self.previous_batch_id.id if self.previous_batch_id else []
        vals['previous_package_id'] = self.previous_package_id.id if self.previous_package_id else []
        vals[
            'previous_course_package_id'] = self.previous_course_package_id.id if self.previous_course_package_id else []
        vals['previous_medium_id'] = self.previous_medium_id.id if self.previous_medium_id.id else []
        vals['joining_academic_year_id'] = self.academic_year.id
        vals['residential_type_id'] = self.residential_type_id.id
        vals['office_type_id'] = self.office_type_id.id
        # Parent Info
        vals['father_name'] = self.father_name
        vals['father_occupation_id'] = self.father_occupation_id.id
        vals['father_mobile'] = self.mobile_one
        vals['father_email'] = self.father_email
        vals['mother_name'] = self.mother_name
        vals['mother_occupation_id'] = self.mother_occupation_id.id
        vals['mother_mobile'] = self.mobile_two
        vals['mother_email'] = self.mother_email
        # Address Details
        vals['street'] = self.street
        vals['zip'] = self.zip
        vals['city_id'] = self.city_id.id
        vals['district_id'] = self.district_id.id
        vals['mandal_id'] = self.mandal_id.id
        vals['state_id'] = self.state_id.id
        vals['country_id'] = self.country_id.id
        vals['temp_street'] = self.temp_street
        vals['temp_zip'] = self.temp_zip
        vals['temp_city_id'] = self.temp_city_id.id
        vals['temp_district_id'] = self.temp_district_id.id
        vals['temp_mandal_id'] = self.temp_mandal_id.id
        vals['temp_state_id'] = self.temp_state_id.id
        vals['temp_country_id'] = self.temp_country_id.id
        # Document Details
        vals['fees_collection_o2m_id'] = [(6, 0, self.fees_collection_o2m_id.ids)]
        vals['enq_grade_doc_ids'] = [(6, 0, self.enq_grade_doc_o2m.ids)]
        vals['enquiry_history_ids'] = [(6, 0, self.enquiry_histroy_o2m.ids)]
        vals['partner_id'] = self.partner_id.id if self.partner_id else None
        stud_obj.write(vals)

    # Purpose: Update Old Student information
    def _update_values(self, student_obj):
        for obj in student_obj:
            # General
            self.partner_id = obj.id
            self.admission_no = obj.admission_no if not self.old_admission_no else ''
            # Student Details
            self.image = obj.image if obj.image else ''
            self.sur_name = obj.sur_name
            self.name = obj.name
            self.gender = obj.gender if obj.gender else False
            self.gender_option = obj.gender if obj.gender else False
            self.dob = obj.date_of_birth if obj.date_of_birth else ''
            self.aadhaar_no = obj.aadhaar_no if obj.aadhaar_no else ''
            self.aadhaar_file = obj.aadhaar_file if obj.aadhaar_file else ''
            self.filename = obj.filename if obj.filename else ''
            self.blood_group_id = obj.blood_group_id.id if obj.blood_group_id else []
            self.religion_id = obj.religion_id.id if obj.religion_id else []
            self.caste_id = obj.caste_id.id if obj.caste_id else []
            self.community_id = obj.community_id.id if obj.community_id else []
            self.academic_year_id = obj.joining_academic_year_id.id if obj.joining_academic_year_id else []
            # Hall ticket Info
            self.hall_ticket_no = obj.hall_ticket_no if obj.hall_ticket_no else ''
            self.board_type_id = obj.board_type_id.id if obj.board_type_id else []
            self.board_code = obj.board_code if obj.board_code else ''
            self.course_opted = obj.course_opted if obj.course_opted else ''
            self.total_marks = obj.total_marks if obj.total_marks else 0
            self.rank = obj.rank if obj.rank else ''
            self.grade = obj.grade if obj.grade else ''
            # Education Info
            self.previous_course_id = obj.course_id.id if obj.course_id else []
            self.previous_group_id = obj.group_id.id if obj.group_id else []
            self.previous_batch_id = obj.batch_id.id if obj.batch_id else []
            self.previous_package_id = obj.package_id.id if obj.package_id else []
            self.previous_course_package_id = obj.course_package_id.id if obj.course_package_id else []
            self.previous_medium_id = obj.medium_id.id if obj.medium_id else []
            # Parent Details
            self.father_name = obj.father_name
            self.mother_name = obj.mother_name
            self.father_occupation_id = obj.father_occupation_id.id if obj.father_occupation_id else []
            self.mother_occupation_id = obj.mother_occupation_id.id if obj.mother_occupation_id else []
            self.mobile_one = obj.father_mobile if obj.father_mobile else ''
            self.mobile_two = obj.mother_mobile if obj.mother_mobile else ''
            self.father_email = obj.father_email if obj.father_name else ''
            self.mother_email = obj.mother_email if obj.mother_email else ''
            # Address Details
            self.street = obj.street if obj.street else ''
            self.city_id = obj.city_id.id if obj.city_id else []
            self.district_id = obj.district_id.id if obj.district_id else []
            self.mandal_id = obj.mandal_id.id if obj.mandal_id else []
            self.state_id = obj.state_id.id if obj.state_id else []
            self.country_id = obj.country_id.id if obj.country_id else []
            self.zip = obj.zip if obj.zip else ''
            self.temp_street = obj.temp_street if obj.temp_street else ''
            self.temp_city_id = obj.temp_city_id.id if obj.temp_city_id else []
            self.temp_district_id = obj.temp_district_id.id if obj.temp_district_id else []
            self.temp_mandal_id = obj.temp_mandal_id.id if obj.temp_mandal_id else []
            self.temp_state_id = obj.temp_state_id.id if obj.temp_state_id else []
            self.temp_country_id = obj.temp_country_id.id if obj.temp_country_id else []
            self.temp_zip = obj.temp_zip if obj.temp_zip else ''
            # Document Details
            # self.fees_collection_o2m_id = [(6, 0, obj.fees_collection_o2m_id.ids)]
            self.enq_grade_doc_o2m = [(6, 0, obj.enq_grade_doc_ids.ids)]
            self.enquiry_histroy_o2m = [(6, 0, obj.enquiry_history_ids.ids)]

    @api.onchange('hall_ticket_no')
    def onchange_hall_ticket_no(self):
        if self.old_new in ['old', 'new'] and self.hall_ticket_no:
            self.hall_ticket_no = self.hall_ticket_no.strip().upper()
            student_obj = self.env['res.partner'].search(
                [('hall_ticket_no', '=', self.hall_ticket_no), ('active', '=', True)], limit=1)
            if student_obj:
                self._update_values(student_obj)

    # Purpose: Old Student information
    @api.onchange('old_new', 'admission_no', 'old_admission_no')
    def _onchange_admission_no(self):
        if self.old_new == 'old' and self.admission_no:
            self.res_no = self.admission_no
            student_obj = self.env['res.partner'].search(
                [('user_type', '=', 'student'), ('admission_no', '=', self.admission_no), ('active', '=', True)])
            if student_obj:
                self._update_values(student_obj)
            if not student_obj:
                raise ValidationError('Please enter the valid admission number')
        elif self.old_admission_no:
            student_obj = self.env['res.partner'].search(
                [('user_type', '=', 'student'), ('admission_no', '=', self.old_admission_no), ('active', '=', True)])
            if student_obj:
                self._update_values(student_obj)
            if not student_obj:
                raise ValidationError('Please enter the valid old admission number')

    """ Calculations for Less Sequence """

    @api.multi
    def _get_less_amount(self, fees_struct):
        course_fee_amount = 0.0;
        less_amount = 0.0
        for line in fees_struct.structure_line_ids:
            if line.fees_id.is_course_fee:
                course_fee_amount = line.v_amount if self.old_new == 'old' else line.new_stud_amount
                break;
        if course_fee_amount > self.res_comm_amount:
            less_amount = course_fee_amount - self.res_comm_amount
        return less_amount

    @api.multi
    def create_fees(self):
        fee_pay_yr = {'one_year': 1, 'two_year': 2, 'three_year': 3}
        fees_coll = self.env['pappaya.fees.collection']
        stud_coll = self.env['student.fees.collection']
        ledger_obj = self.env['pappaya.fees.ledger']
        ledger_obj_line = self.env['pappaya.fees.ledger.line']
        if self.package_id:
            fees_struct = self.env['pappaya.fees.structure'].search([('academic_year_id', '=', self.academic_year.id),
                                                                     ('school_id', '=', self.branch_id.id),
                                                                     ('course_id', '=', self.course_id.id),
                                                                     ('group_id', '=', self.group_id.id),
                                                                     ('batch_id', '=', self.batch_id.id),
                                                                     ('package_id', '=', self.package.id),
                                                                     ('residential_type_id', '=',
                                                                      self.residential_type_id.id),
                                                                     ('type', '=', self.course_id.type)])
            search_fees = fees_coll.search([('enquiry_id', '=', self.id)])
            course_uniform = self.env['pappaya.uniform'].search([('academic_year_id', '=', self.academic_year.id),
                                                                 ('school_id', '=', self.branch_id.id),
                                                                 ('course_id', '=', self.course_id.id),
                                                                 ('gender', '=', self.gender)])
            coll_id = None
            reservation_amount = 0.0
            reservation_pay_status = ''
            reservation_head = None
            if search_fees:
                coll_id = search_fees
                for s in search_fees.fees_collection_line:
                    if s.term_state == 'processing':
                        raise ValidationError('In that Reservation Stage Cheque/DD needs be cleared..!')
                    if s.name.is_reservation_fee and s.term_state == 'paid':
                        reservation_head = s
                        reservation_amount = s.total_paid
                        reservation_pay_status = s.term_state

            else:
                coll_id = fees_coll.create({'enquiry_id': self.id,
                                            'school_id': self.branch_id.id,
                                            'academic_year_id': self.academic_year.id,
                                            'bulk_term_state': 'due',
                                            'collection_date': datetime.today().date()})
            # reservation_fee = 0.0
            f_amount = 0.0
            status = 'due'
            ledger_id = None
            ledger = ledger_obj.search([('fee_collection_id', '=', coll_id.id)])
            ledger_id = ledger
            if not ledger:
                ledger = ledger_obj.sudo().create({
                    'admission_number': coll_id.admission_number,
                    'enquiry_id': coll_id.enquiry_id.id,
                    'fee_collection_id': coll_id.id,
                    'school_id': coll_id.school_id.id,
                    'academic_year_id': coll_id.academic_year_id.id,
                    'enquiry_no': coll_id.enquiry_id.id,
                    'course_id': coll_id.enquiry_id.course_id.id,
                    'group_id': coll_id.enquiry_id.group_id.id,
                    'batch_id': coll_id.enquiry_id.batch_id.id,
                    'package': coll_id.enquiry_id.package.id,
                    'package_id': coll_id.enquiry_id.package_id.id
                })
                ledger_id = ledger

            # Less AMount
            less_amount = self._get_less_amount(fees_struct)
            les_next_sequence = 1

            reservation_fee = 0.0
            reservation_adj_heads = []

            for i in fees_struct:
                for j in i.structure_line_ids:
                    # if j.fees_id.is_reservation_fee:
                    #     reservation_fee = j.amount
                    if self.old_new == 'old':
                        j_amount = j.v_amount
                        j_gst_amount = j.total
                    else:
                        j_amount = j.new_total
                        j_gst_amount = j.new_stud_amount

                    # Uniform Fee Amount fetch from branch wise uniform
                    if not course_uniform and j.fees_id.is_uniform_fee:
                        continue
                    if course_uniform:
                        if j.fees_id.is_uniform_fee:
                            j_amount = course_uniform.total_amount
                            j_gst_amount = course_uniform.total_amount

                    # Nslate Fee Check
                    if j.fees_id.is_nslate_fee and self.is_nslate_required == 'no':
                        continue
                    if self.nslate_item_ids and self.is_nslate_required == 'yes':
                        if j.fees_id.is_nslate_fee:
                            j_amount = self.nslate_amount
                            j_gst_amount = self.nslate_amount

                    # Library Fee Amount fetch from Branch
                    if j.fees_id.is_library_fee and not self.branch_id.is_library_fee:
                        continue
                    if j.fees_id.is_library_fee and self.branch_id.is_library_fee:
                        j_amount = self.branch_id.library_fee_amount
                        j_gst_amount = self.branch_id.library_fee_amount

                    # Material Fee Amount fetch from Course Package
                    if not self.material_set_ids and j.fees_id.is_material_fee:
                        continue
                    if self.material_set_ids:
                        if j.fees_id.is_material_fee:
                            j_amount = self.material_amt
                            j_gst_amount = self.material_amt

                    # Transport fee Amount fetch from slab amount
                    if j.fees_id.is_transport_fee and self.is_transport_required == 'no':
                        continue

                    if self.residential_type_id.code != 'hostel' and self.is_transport_required == 'yes':
                        if j.fees_id.is_transport_fee:
                            j_amount = self.transport_slab_id.amount
                            j_gst_amount = self.transport_slab_id.amount

                    if j.fees_id.is_reservation_fee and self.sponsor_type == 'yes':
                        j_amount = 0.0

                    if not j.fees_id.is_course_fee:
                        if (j.fees_id.gender == 'both' or self.gender == j.fees_id.gender) \
                                and (self.residential_type_id.id in j.fees_id.residential_type_ids.ids) \
                                and (self.medium_id.id in j.fees_id.medium_ids.ids):

                            # Less Sequence
                            if less_amount > 0.0 and j.less_sequence == les_next_sequence:
                                les_next_sequence += 1
                                if j_amount <= less_amount:
                                    j_amount = 0.0;
                                    less_amount -= j_amount
                                else:
                                    j_amount -= less_amount
                            if j_amount <= reservation_amount:
                                f_amount = j_amount
                                reservation_amount -= j_amount
                                status = reservation_pay_status
                                ####### 2 year course fee feature ######
                                if j.fees_id.is_course_fee_component:
                                    j_amount = j_amount * fee_pay_yr[self.fees_opt_for]
                                ######## End##############3

                                tax_ids = [(6, 0, j.tax_ids.ids)]
                                tax_compt = j.tax_ids.compute_all(j_amount, None, 1, None, None)
                                t_amt = tax_compt['taxes'][0]['amount'] if len(tax_compt['taxes']) > 0 else 0.0
                                total_included = tax_compt['total_included']
                                total_excluded = tax_compt['total_excluded']

                                fee_line = stud_coll.create({
                                    'collection_id': coll_id.id,
                                    'name': j.fees_id.id,
                                    'gst_total': total_excluded, #j.total if self.old_new == 'old' else j.new_stud_amount,
                                    'tax_ids': tax_ids,
                                    'cgst': t_amt,
                                    'sgst': t_amt,
                                    'amount': total_included,
                                    'res_adj_amt': f_amount,  # reservation_amount,
                                    'due_amount': 0.00,
                                    'total_paid': 0.00,  # if reservation_amount > 0.0 else 0.0,
                                    # (j_amount - f_amount) if reservation_amount > 0.0 else j.amount,
                                    'term_state': status,
                                    'enquiry_id': self.id,
                                    'less_sequence': j.less_sequence,
                                })
                                if fee_line.res_adj_amt > 0.00:
                                    reservation_adj_heads.append(fee_line.id)
                                ledger_obj_line.create({
                                    'fee_line_id': fee_line.id,
                                    'credit': fee_line.amount,
                                    'concession_amount': fee_line.concession_amount,
                                    'concession_type_id': fee_line.concession_type_id.id,
                                    'debit': fee_line.total_paid,
                                    'balance': fee_line.amount - (fee_line.total_paid + fee_line.concession_amount),
                                    'fees_ledger_id': ledger_id.id,
                                    'res_adj_amt': fee_line.res_adj_amt,
                                })
                            else:
                                d_amount = j_amount - reservation_amount
                                status = 'due'
                                ####### 2 year course fee feature ######
                                if j.fees_id.is_course_fee_component:
                                    j_amount = j_amount * fee_pay_yr[self.fees_opt_for]
                                ######## End##############3
                                tax_ids = [(6, 0, j.tax_ids.ids)]
                                tax_compt = j.tax_ids.compute_all(j_amount, None, 1, None, None)
                                t_amt = tax_compt['taxes'][0]['amount'] if len(tax_compt['taxes']) >0 else 0.0
                                total_included = tax_compt['total_included']
                                total_excluded = tax_compt['total_excluded']


                                fee_line = stud_coll.create({
                                    'collection_id': coll_id.id,
                                    'name': j.fees_id.id,
                                    'gst_total': total_excluded, #j.total if self.old_new == 'old' else j.new_stud_amount,
                                    'tax_ids' : tax_ids,
                                    'cgst': t_amt,
                                    'sgst': t_amt,
                                    'amount': total_included,
                                    'res_adj_amt': reservation_amount,
                                    'due_amount': d_amount,
                                    'total_paid': 0.00,  # if reservation_amount > 0.0 else 0.0,
                                    # (j_amount - f_amount) if reservation_amount > 0.0 else j.amount,
                                    'term_state': status,
                                    'enquiry_id': self.id,
                                    'less_sequence': j.less_sequence,
                                })
                                if fee_line.res_adj_amt > 0.00:
                                    reservation_adj_heads.append(fee_line.id)
                                reservation_amount = 0.0
                                ledger_obj_line.create({
                                    'fee_line_id': fee_line.id,
                                    'credit': fee_line.amount,
                                    'concession_amount': fee_line.concession_amount,
                                    'concession_type_id': fee_line.concession_type_id.id,
                                    'debit': fee_line.total_paid,
                                    'balance': fee_line.amount - (fee_line.total_paid + fee_line.concession_amount),
                                    'fees_ledger_id': ledger_id.id,
                                    'res_adj_amt': fee_line.res_adj_amt,
                                })
                    else:
                        if (j.fees_id.gender == 'both' or self.gender == j.fees_id.gender) \
                                and (self.residential_type_id.id in j.fees_id.residential_type_ids.ids) \
                                and (self.medium_id.id in j.fees_id.medium_ids.ids):
                            if j.fees_id.is_course_fee:
                                #                                 res_paid_amt = 0.00
                                # 	                            state = 'due'
                                # 	                            if reservation_amount > 0.00:
                                # 	                                if self.res_comm_amount <= reservation_amount:
                                # 	                                    res_paid_amt = self.res_comm_amount
                                # 	                                    reservation_amount -= res_paid_amt
                                # 	                                    state = reservation_pay_status
                                # 	                                else:
                                # 	                                    res_paid_amt = reservation_amount
                                # 	                                    reservation_amount -= reservation_amount
                                # 	                                    state = 'due'
                                # 	                            sgst, cgst, gst_total = 0.0, 0.0, 0.0
                                # 	                            if self.res_comm_amount:
                                # 	                                sgst = (self.res_comm_amount * self.course_id.sgst) / 100 if self.course_id.sgst else 0.0
                                # 	                                cgst = ( self.res_comm_amount * self.course_id.cgst) / 100 if self.course_id.cgst else 0.0
                                # 	                                gst_total = sgst + cgst
                                course_fee_total = 0.0;
                                course_fee_paid_total = 0.0
                                for line in coll_id.fees_collection_line:
                                    if line.name.is_course_fee_component:
                                        course_fee_total += line.amount
                                        course_fee_paid_total += line.total_paid + line.res_adj_amt

                                tax_ids = [(6, 0, j.tax_ids.ids)]
                                tax_compt = j.tax_ids.compute_all(course_fee_total, None, 1, None, None)
                                t_amt = tax_compt['taxes'][0]['amount'] if len(tax_compt['taxes']) > 0 else 0.0
                                total_included = tax_compt['total_included']
                                total_excluded = tax_compt['total_excluded']

                                fee_line = stud_coll.create({
                                    'collection_id': coll_id.id,
                                    'name': j.fees_id.id,
                                    'amount': total_included,
                                    'total_paid': course_fee_paid_total,
                                    'due_amount': course_fee_total - course_fee_paid_total,
                                    'term_state': 'due',
                                    'enquiry_id': self.id,
                                    'res_adj_amt': 0.0,
                                    'gst_total': total_excluded , #self.res_comm_amount - gst_total,
                                    'tax_ids' : tax_ids,
                                    'sgst': t_amt,
                                    'cgst': t_amt,
                                    'less_sequence': j.less_sequence,
                                })
                                if fee_line.res_adj_amt > 0.00:
                                    reservation_adj_heads.append(fee_line.id)
                                ledger_obj_line.create({
                                    'fee_line_id': fee_line.id,
                                    'credit': fee_line.amount,
                                    'concession_amount': fee_line.concession_amount,
                                    'concession_type_id': fee_line.concession_type_id.id,
                                    'debit': fee_line.total_paid,
                                    'balance': fee_line.amount - (fee_line.total_paid + fee_line.concession_amount),
                                    'fees_ledger_id': ledger_id.id,
                                    'res_adj_amt': fee_line.res_adj_amt,
                                })
            if reservation_adj_heads:
                self.env['pappaya.fees.collection'].reservartion_adjustment_receipt_ledger(coll_id, reservation_head,
                                                                                           reservation_adj_heads)
            if reservation_amount > 0.00:
                res_ledger_due_amt = 0.00
                for fees_collect_line in coll_id.fees_collection_line:
                    if fees_collect_line.name.is_reservation_fee:
                        fees_collect_line.res_adj_amt_extra = reservation_amount
                        fees_collect_line.due_amount = reservation_amount
                        res_ledger_due_amt = reservation_amount
                        reservation_amount = 0.00
                for fees_collect_line in ledger.fee_ledger_line:
                    if fees_collect_line.fee_line_id.name.is_reservation_fee:
                        fees_collect_line.due_amount = res_ledger_due_amt

        return True

    @api.model
    def notify_grade_joining_document(self):
        # template_id = self.env.ref('pappaya_admission.email_template_grade_joining_document_followup')
        # today = fields.date.today()
        # for record in self.search([]):
        #     if record.branch_id.last_execution_date:
        #         run_date = datetime.strptime(record.branch_id.last_execution_date, '%Y-%m-%d').date() + \
        #                    timedelta(days=record.branch_id.document_followup)
        #     else:
        #         run_date = None
        #     docs_list = [i.document_name for i in record.enq_grade_doc_o2m if not i.document_file]
        #     if (record.branch_id.document_followup != 0 and not record.branch_id.last_execution_date) \
        # 		or today == run_date :
        #          if docs_list:
        #               template_id.send_mail(record.id)
        #               record.branch_id.last_execution_date = today
        return True
    
    def unlink(self):
        raise ValidationError("Sorry You cannot delete admission record.")
        return super(PappayaAdmission, self).unlink()
    
    def copy(self):
        raise ValidationError("Sorry you cannot duplicate admission record.")
        return super(PappayaAdmission, self).copy()

    @api.multi
    def create_six_acc_journal_ent(self):
        return True

    @api.multi
    def _get_move_lines_from_adj(self, student_obj, fee_head_obj, amount_paid, journal_obj, collection_id):
        move_lines = []
        operating_unit_obj = collection_id.school_id
        # if not self.payment_mode_id.debit_account_id:
        #     raise ValidationError('Please configure Debit account in payment mode')
        # debit_acc_id = self.env['pappaya.fees.head'].search([('is_reservation_fee','=',True)]).debit_account_id
        move_lines.append((0, 0, {
            'name': fee_head_obj.name,  # a label so accountant can understand where this line come from
            'debit': 0,
            'credit': amount_paid,
            'account_id': fee_head_obj.credit_account_id.id,  # Course Fee chart of account.
            'date': str(datetime.today().date()),
            'partner_id': student_obj.id,
            'journal_id': journal_obj.id,  # Cash journal
            'company_id': journal_obj.company_id.id,
            'currency_id': journal_obj.company_id.currency_id.id,
            'date_maturity': str(datetime.today().date()),
            'operating_unit_id': operating_unit_obj.id,
            'fees_collection_id': collection_id.id,
        }))
        # move_lines.append((0, 0, {
        #     'name': student_obj.name,
        #     'debit': amount_paid,
        #     'credit': 0,
        #     # 'account_id': student_obj.property_account_receivable_id.id,# Student account
        #     # ~ 'account_id': fee_head_obj.contra_account_id.id,# Contra Ledger
        #     'account_id': debit_acc_id.id,  # Contra Ledger
        #     'date': str(datetime.today().date()),
        #     'partner_id': student_obj.id,
        #     'journal_id': journal_obj.id,
        #     'company_id': journal_obj.company_id.id,
        #     'currency_id': journal_obj.company_id.currency_id.id,  # currency id of narayana
        #     'date_maturity': str(datetime.today().date()),
        #     'operating_unit_id': operating_unit_obj.id,
        #     'fees_collection_id': collection_id.id,
        # }))
        return move_lines

    @api.multi
    def _create_move_entry_from_adj(self, journal_obj, operating_unit_obj, line_ids):
        account_move_obj = self.env['account.move'].create({
            'journal_id': journal_obj.id,  # journal ex: sale journal, cash journal, bank journal....
            'date': str(datetime.today().date()),
            'state': 'draft',
            'company_id': journal_obj.company_id.id,
            'operating_unit_id': operating_unit_obj.id,
            'line_ids': line_ids,  # this is one2many field to account.move.line
        })
        return account_move_obj


class PappayaNslateItem(models.Model):
    _name = "pappaya.nslate.item"

    @api.constrains('price_unit')
    def check_price_unit(self):
        if self.price_unit <= 0.0:
            raise ValidationError('Please enter the valid Nslate Price..!')

    @api.constrains('product_id')
    def check_product(self):
        if len(self.search([('admission_id', '=', self.admission_id.id), ('product_id', '=', self.product_id.id)])) > 1:
            raise ValidationError('Nslate Item already exist..!')

    admission_id = fields.Many2one('pappaya.admission', string="Admission", ondelete="cascade")
    sequence = fields.Integer(string='Sequence')
    product_id = fields.Many2one('product.product', string='Nslate Item', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict')
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure')
    price_unit = fields.Float('Per Unit Price', related='product_id.lst_price', digits=dp.get_precision('Price'))
    price_subtotal = fields.Float(string='Subtotal', compute='compute_price')

    @api.depends('product_uom_qty', 'price_unit')
    def compute_price(self):
        for rec in self:
            rec.price_subtotal = rec.product_uom_qty * rec.price_unit


class AdmissionUniform(models.Model):
    _name = "admission.uniform"
    _description = "Admission Uniform"

    @api.constrains('price_unit')
    def check_price_unit(self):
        if self.price_unit <= 0.0:
            raise ValidationError('Please enter the valid Uniform Price..!')

    @api.constrains('product_id')
    def check_product(self):
        if len(self.search([('admission_id', '=', self.admission_id.id), ('product_id', '=', self.product_id.id)])) > 1:
            raise ValidationError('Uniform Item already exist..!')

    admission_id = fields.Many2one('pappaya.admission', string="Admission", ondelete="cascade")
    sequence = fields.Integer(string='Sequence')
    from_uniform_set = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='From Uniform Set', default='no')
    product_id = fields.Many2one('product.product', string='Uniform Item', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict')
    product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True,
                                   default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure')
    price_unit = fields.Float('Per Unit Price', related='product_id.lst_price',
                              digits=dp.get_precision('Uniform Price'))
    price_subtotal = fields.Float(string='Subtotal', compute='compute_price')

    @api.depends('product_uom_qty', 'price_unit')
    def compute_price(self):
        for rec in self:
            rec.price_subtotal = rec.product_uom_qty * rec.price_unit


class pappaya_other_payment(models.Model):
    _inherit = 'pappaya.other.payment'
    
    @api.multi
    @api.onchange('material_set_ids')
    @api.depends('material_set_ids.price_subtotal')
    def onchange_material_set_ids(self):
        for record in self:
            amount = 0.0
            for item in record.material_set_ids:
                amount += item.price_subtotal
            record.amount = amount

    admission_id = fields.Many2one('pappaya.admission', 'Admission No')
    course_package_id = fields.Many2one(comodel_name='pappaya.course.package', related='admission_id.package_id',
                                        string='Course Package')
    material_set_ids = fields.Many2many('branchwise.material.line', string='Material Set')

    @api.onchange('admission_id')
    @api.depends('admission_id')
    def onchange_admission_no(self):
        warning = {}
        if self.admission_id:
            self.student_id = self.admission_id.partner_id.id;
            self.branch_id = self.admission_id.branch_id.id
            self.father_name = self.admission_id.father_name


class old_student_pending_fees_wizard(models.TransientModel):
    _name = 'old.student.pending.fees.wizard'

    status = fields.Text('Status')
    fee_collection_id = fields.Many2one('pappaya.fees.collection', 'Fee')

    @api.model
    def default_get(self, fields):
        res = super(old_student_pending_fees_wizard, self).default_get(fields)
        if 'fee_collection_id' in self._context and self._context['fee_collection_id']:
            res['fee_collection_id'] = int(self._context.get('fee_collection_id'))
            fee_colleciton_obj = self.env['pappaya.fees.collection'].search(
                [('id', '=', self._context.get('fee_collection_id'))])
            if 'hall_ticket_number' in self._context and self._context['hall_ticket_number']:
                res['status'] = "For given Hall ticket number (" + str(
                    self._context['hall_ticket_number']) + ") having pending fees amount Rs. " + str(
                    self._context.get('total_pending_fee')) + "\n\nKindly Pay pending fees to proceed admission."
            else:
                res['status'] = "For given admission number (" + str(
                    self._context['admission_number']) + ") having pending fees amount Rs. " + str(
                    self._context.get('total_pending_fee')) + "\n\nKindly Pay pending fees to proceed admission."
        return res

    @api.multi
    def open_fees_collection(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pappaya.fees.collection',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.fee_collection_id.id,
            'view_id': self.env.ref('pappaya_fees.pappaya_fees_collection_form', False).id,
            'target': 'new',
        }
