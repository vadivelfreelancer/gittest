
import logging
from ast import literal_eval
from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from odoo import tools, api
from odoo.exceptions import ValidationError
import re

import serial
BAUD_RATE = 9600
BIO_BYTES1 = 4

_logger = logging.getLogger(__name__)
import socket
HOST = '172.20.200.163' # Enter IP or Hostname of your server
PORT = 1500 # Pick an open Port (1000+ recommended), must match the server port

class PappayaStudent(models.Model):
    _name = "res.partner"
    _inherit = ['res.partner', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'student_full_name'
    _order = 'admission_no asc'
    _description = 'Pappaya Student'

    user_type = fields.Selection([('student','Student')], string='User Type')
    form_no = fields.Char(string='Form No')
    admission_no = fields.Char(string='Admission No')
    sur_name = fields.Char('Sur Name', size=40, track_visibility="onchange")
    name = fields.Char('Name', track_visibility="onchange")
    joining_academic_year_id = fields.Many2one('academic.year', string="Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    date_of_birth = fields.Date('Date of Birth')
    date_of_joining = fields.Date('Date of Joining')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Gender')
    blood_group_id = fields.Many2one('pappaya.master', string='Blood Group', track_visibility="onchange")
    caste_id = fields.Many2one('pappaya.master', string="Caste", track_visibility="onchange")
    religion_id = fields.Many2one('pappaya.master', string="Religion", track_visibility="onchange")
    community_id = fields.Many2one('pappaya.master', string="Community", track_visibility="onchange")
    aadhaar_no = fields.Char('Aadhaar Number', size=12)
    aadhaar_file = fields.Binary('Aadhaar Upload', track_visibility="onchange")
    filename = fields.Char(string='Filename')
    father_name = fields.Char("Father Name")
    father_mobile = fields.Char("Father Mobile", size=10, track_visibility="onchange")
    father_email = fields.Char("Father Email", track_visibility="onchange")
    father_occupation_id = fields.Many2one('pappaya.master', string="Father Occupation", track_visibility="onchange")
    mother_name = fields.Char("Mother Name")
    mother_mobile = fields.Char("Mother Mobile", size=10, track_visibility="onchange")
    mother_email = fields.Char("Mother Email", track_visibility="onchange")
    mother_occupation_id = fields.Many2one('pappaya.master', string="Mother Occupation", track_visibility="onchange")
    street = fields.Char('Street', track_visibility="onchange")
    city_id = fields.Many2one('pappaya.city', string='City', track_visibility="onchange")
    district_id = fields.Many2one('state.district', string='District', track_visibility="onchange")
    mandal_id = fields.Many2one('pappaya.mandal.marketing', string='Mandal', track_visibility="onchange")
    state_id = fields.Many2one('res.country.state', string="State", domain=[('country_id.is_active', '=', True)], track_visibility="onchange")
    country_id = fields.Many2one('res.country', string="Country", track_visibility="onchange", default=lambda self: self.env['res.country'].sudo().search([('code', '=', 'IN'), ('is_active', '=', True)], limit=1).id)
    zip = fields.Char(string='Zipcode', size=6, track_visibility="onchange")
    temp_street = fields.Char('Street', track_visibility="onchange")
    temp_city_id = fields.Many2one('pappaya.city', string='City', track_visibility="onchange")
    temp_district_id = fields.Many2one('state.district', string='District', track_visibility="onchange")
    temp_mandal_id = fields.Many2one('pappaya.mandal.marketing', string='Mandal', track_visibility="onchange")
    temp_state_id = fields.Many2one('res.country.state', string="State", domain=[('country_id.is_active', '=', True)], track_visibility="onchange")
    temp_country_id = fields.Many2one('res.country', string="Country", track_visibility="onchange", default=lambda self: self.env['res.country'].sudo().search([('code', '=', 'IN'), ('is_active', '=', True)], limit=1).id)
    temp_zip = fields.Char('Zipcode', size=6, track_visibility="onchange")
    student_type = fields.Selection([('day', 'Day'),('hostel', 'Hostel'),('semi_residential','Semi Residential')], string='Student Type')
    residential_type_id = fields.Many2one('residential.type', 'Student Residential Type')
    school_id = fields.Many2one('operating.unit', string='Branch')
    course_id = fields.Many2one('pappaya.course', string='Course')
    group_id = fields.Many2one('pappaya.group', string='Group')
    batch_id = fields.Many2one('pappaya.batch', string='Batch')
    package_id = fields.Many2one('pappaya.package', string='Package')
    course_package_id = fields.Many2one('pappaya.course.package', string='Course Package')
    medium_id = fields.Many2one('pappaya.master', string='Medium')
    office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    previous_school_id = fields.Many2one('res.company', string='Branch')
    previous_course_id = fields.Many2one('pappaya.course', string='Course')
    previous_group_id = fields.Many2one('pappaya.group', string='Group')
    previous_batch_id = fields.Many2one('pappaya.batch', string='Batch')
    previous_package_id = fields.Many2one('pappaya.package', string='Package')
    previous_course_package_id = fields.Many2one('pappaya.course.package', string='Course Package')
    previous_medium_id = fields.Many2one('pappaya.master', string='Medium')
    hall_ticket_no = fields.Char('Hall Ticket No')
    board_type_id = fields.Many2one('pappaya.master', string="Board Type")
    board_code = fields.Char(string='Board Code', related='board_type_id.code')
    course_opted = fields.Selection([('junior', 'Junior'), ('senior', 'Senior'), ('mpc', 'M.P.C'), ('bipc', 'Bi.P.C'), ('civils', 'CIVILS')],string='Course Opted')
    total_marks = fields.Float(string='Total Marks')
    rank = fields.Char(string='Rank', size=5)
    grade = fields.Char(string='Grade')
    rfid_card_no = fields.Char('Attendance RFID Card No.')
    canteen_rf_card_id = fields.Char('Wallet RF ID')
    biometric_id = fields.Char('Wallet Biometric ID')
    student_wallet_amount = fields.Float('Pocket Money', track_visibility="onchange")
    partner_id = fields.Many2one('res.partner', 'Partner', ondelete="cascade")
    admission_id = fields.Many2one('pappaya.admission', string="Admission")
    enquiry_history_ids = fields.Many2many('pappaya.enq.workflow.history', string='History')
    enq_grade_doc_ids = fields.Many2many('pappaya.enq.grade_doc', string='Grade Joining Document')
    student_full_name = fields.Char('Student Name', size=150)
    update_fullname = fields.Boolean(compute='_get_student_fullname')
    fees_collection_o2m_id = fields.One2many('student.fees.collection', 'student_id', string='Fees Collection')
    transport_history_ids = fields.One2many('pappaya.transport.history', 'student_id', string='Transport History')
    is_transport = fields.Boolean(related='school_id.is_transport', string='Is Transport?')
    caution_deposit = fields.Float(string='Caution Deposit')
    cancel = fields.Boolean(related='admission_id.cancel', string='Cancel', store=True)

    @api.multi
    @api.depends('student_full_name', 'admission_no')
    def name_get(self):
        result = []
        for stud in self:
            if stud.student_full_name and stud.admission_no:
                name = '(' + str(stud.admission_no) + ') ' + str(stud.student_full_name)
            else:
                name = stud.name
            result.append((stud.id, name))
        return result

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
    
    @api.onchange('hall_ticket_no')
    def onchange_hall_ticket_no(self):
        if self.hall_ticket_no:
            self.hall_ticket_no = self.hall_ticket_no.strip().upper()

    @api.constrains('date_of_birth')
    def _check_dob(self):
        if self.date_of_birth:
            d1 = datetime.strptime(self.date_of_birth, "%Y-%m-%d").date()
            d2 = date.today()
            rd = relativedelta(d2, d1)
            age = str(rd.years) + ' years'
            if rd.years > 60:
                raise ValidationError('Age should not exceed more than 60 Years')

    @api.onchange('city_id')
    def _onchange_city(self):
        domain = []
        if self.city_id:
            city_obj = self.env['pappaya.city'].search([('id','=', self.city_id.id)])
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
    def copy(self, default=None):
        raise ValidationError('Sorry, You are not allowed to Duplicate')

    @api.multi
    def unlink(self):
        raise ValidationError("Sorry, You are not allowed to Delete.")

    @api.multi
    def action_view_partner_invoices(self):
        self.ensure_one()
        action = self.env.ref('account.action_invoice_refund_out_tree').read()[0]
        action['domain'] = literal_eval(action['domain'])
        action['domain'].append(('partner_id', 'child_of', self.partner_id.id))
        return action

    @api.multi
    def enroll_rf_id(self):
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'enroll.rf.id',
            'target': 'new',
            'context':self.ids
        }


class enroll_rf_id(models.TransientModel):
    _name='enroll.rf.id'
    _description='Enroll RF ID'
    
    student_id = fields.Many2one('res.partner', domain=[('user_type','=','student')])
    canteen_rf_card_id = fields.Char('Wallet RF ID')
    biometric_id = fields.Char('Wallet Biometric ID')
    message = fields.Char('Status', default="Click Enroll and scan your RF ID.")
    
    @api.model
    def default_get(self, fields):
        res = super(enroll_rf_id, self).default_get(fields)
        res['student_id'] = self._context.get('active_ids')[0] if self._context.get('active_ids') else False
        return res
    
    def update_rf_id(self):
        for record in self:
            self.message = "Please Scan RF ID"
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((HOST,PORT))
                print ("SCANNIG RFID")
                command = b'3'
                s.send(command)
                reply = s.recv(1024)
                if reply:
                    record.student_id.canteen_rf_card_id = str(reply)[1:]
                self.message = 'Place your Finger'
                while True:
                    if record.student_id.canteen_rf_card_id:
                        command2 = b'1'
                        self.message = "Please Scan Biometric"
                        print ("Please Scan Biometric")
                        s.send(command2)
                        reply = s.recv(1024)
                        try:
                            int(reply[1:])
                            record.student_id.biometric_id = str(reply)[1:]
                            break
                        except:
                            continue
                self.message = "Enroll is done."
            except:
                raise ValidationError("Finger mismatched.. try again..")

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            if not re.match('^[a-zA-Z\d\s]*$', self.name):
                raise ValidationError('Please enter a valid Name.')
            self.name = (str(self.name).strip()).upper()

    @api.onchange('card_number')
    def onchange_card_number(self):
        if self.card_number:
            match_number = re.match('^[\d]*$', self.card_number)
            if not match_number or len(self.card_number) != 16:
                raise ValidationError('Please enter a valid card number.')

    @api.model
    def create(self, vals):
        if 'name' in vals.keys() and vals.get('name'):
            if not re.match('^[a-zA-Z\d\s]*$', vals.get('name')):
                raise ValidationError('Please enter a valid Name.')
            vals.update({'name': str(vals.get('name').strip()).upper()})
        if 'card_number' in vals.keys() and vals.get('card_number'):
            match_number = re.match('^[\d]*$', vals.get('card_number'))
            if not match_number or len(vals.get('card_number')) != 16:
                raise ValidationError('Please enter a valid card number.')
            vals.update({'card_number': vals.get('card_number').strip()})
        return super(enroll_rf_id, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'name' in vals.keys() and vals.get('name'):
            if not re.match('^[a-zA-Z\d\s]*$', vals.get('name')):
                raise ValidationError('Please enter a valid Name.')
            vals.update({'card_number': str(vals.get('name').strip()).upper()})
        if 'card_number' in vals.keys() and vals.get('card_number'):
            match_number = re.match('^[\d]*$', vals.get('card_number'))
            if not match_number or len(vals.get('card_number')) != 16:
                raise ValidationError('Please enter a valid card number.')
            vals.update({'card_number': vals.get('card_number').strip()})
        return super(enroll_rf_id, self).write(vals)


class TransportHistory(models.Model):
    _name = 'pappaya.transport.history'
    _description = 'Transport History'

    branch_id = fields.Many2one('operating.unit', string='Branch')
    academic_year_id = fields.Many2one('academic.year', string="Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))
    transport_slab_id = fields.Many2one('pappaya.transport.stop', string='Transport Slab')
    route_id = fields.Many2one('pappaya.transport.route', 'Route')
    service_id = fields.Many2one('pappaya.branch.wise.service', 'Service', related='route_id.service_id', store=True)
    active = fields.Boolean('Active')
    student_id = fields.Many2one('res.partner', string='Student')
