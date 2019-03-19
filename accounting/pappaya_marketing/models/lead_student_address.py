# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import ValidationError
from odoo import SUPERUSER_ID
import re
import roman
roman_pattern='^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$'

def sort_roman_letters(roman_list):
    list_integer = []; sorted_list=[]
    [list_integer.append(roman.fromRoman(str(roman_letter).upper())) for roman_letter in roman_list];list_integer.sort()
    [sorted_list.append(roman.toRoman(number)) for number in list_integer]
    return sorted_list

class pappaya_lead_stud_address(models.Model):
    _name='pappaya.lead.stud.address'
    _description = "Lead Student Address"
    _rec_name = 'sequence'
    _order = 'sequence desc'
        
    @api.model
    def _compute_sequence(self):
        prefix = ''
        sequence = 'New'
        active_academic_year = self.env['academic.year'].search([('is_active','=',True)], limit=1)
        if active_academic_year:
            date_split = active_academic_year.start_date.split('-')
            prefix = date_split[0][2:]
            if prefix:
                students_details = self.search([('academic_year_id', '=', active_academic_year.id)]).ids
                sequence_no =  len(students_details) + 1
                sequence_no = "%0.5d" % sequence_no
                sequence = str(prefix) + '5' + sequence_no
        return sequence
    
    record_id = fields.Integer('Record ID')
    payroll_branch_id = fields.Many2one('pappaya.payroll.branch', 'Payroll Branch')
    branch_id = fields.Many2one('res.company', 'Admission Branch')
    academic_year_id = fields.Many2one('academic.year', "Academic Year", default=lambda self: self.env['academic.year'].search([('is_active', '=', True)]))                                
    sequence = fields.Char(string='Unique ID', default=_compute_sequence)
    employee_id = fields.Many2one('hr.employee', string='PRO')
    name = fields.Char('Student Name',size=100)
    mobile = fields.Char('Mobile', size=10)
    studying_course_id = fields.Many2one('pappaya.lead.course', string="Present Class")
    pro_payroll_state = fields.Many2one('res.country.state', related='employee_id.payroll_branch_id.state_id', string='PRO Payroll State')
    father_name = fields.Char('Father Name',size=100)
    location_type = fields.Selection([('urban','Urban'), ('rural','Rural')], string='Location Type', default='urban')
    state_id  = fields.Many2one('res.country.state', string='State')
    district_id = fields.Many2one('state.district', string='District')
    city = fields.Char('City',size=50)
    mandal = fields.Char('Mandal',size=50)
    ward = fields.Char('Ward',size=50)
    area = fields.Char('Area',size=50)
    mandal = fields.Char('Mandal',size=50)
    village = fields.Char('Village',size=50)
    pincode = fields.Char('Pin Code', size=6)
    studying_school_name = fields.Char(string='School Name',size=100)
    status = fields.Selection([('valid','Valid'),('invalid','Invalid')], 'Status', default='invalid')
    file_name = fields.Char('File Name',size=100)
    
#     gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
#     city_id = fields.Many2one('pappaya.city', string='City')
#     ward_id = fields.Many2one('pappaya.ward', string='Ward')
#     area_id = fields.Many2one('pappaya.area', string='Area')
#     mandal_id = fields.Many2one('pappaya.mandal.marketing', string='Mandal')
#     village_id = fields.Many2one('pappaya.village', string='Village')
#     school_state_id = fields.Many2one('res.country.state', string='School State')
#     school_district_id = fields.Many2one('state.district', string='School District')
#     school_mandal_id = fields.Many2one('pappaya.mandal.marketing', string='School Mandal')
#     lead_school_id = fields.Many2one('pappaya.lead.school',string='School')

    @api.constrains('record_id')
    def validate_duplicate(self):
        if self.record_id and self.record_id > 0:
            if self.sudo().search_count([('record_id','=',self.record_id)]) > 1:
                raise ValidationError("Given record Id already exists.")
    
    @api.onchange('location_type')
    def _onchange_location_type(self):
        if self.location_type:
            self.city = ''; self.ward = ''; self.area = '';
            self.mandal = ''; self.village = ''
    
    @api.multi
    def validate(self):
        for record in self:
            record.status = record.validate_record()
    
    @api.multi
    def reset(self):
        for record in self:
            record.status = 'invalid'

    @api.multi
    def default_status(self):
        for record in self:
            state = 'invalid'
            if record.branch_id and record.employee_id and record.name and record.mobile \
                    and record.studying_course_id and record.state_id and record.district_id:
                state = 'valid'
            if record.name:
                name = self.env['res.company']._validate_name(record.name)
                record.name = name
            if record.pincode:
                invalid_pincode_list = ['000000','111111','222222','333333','444444','555555','666666','777777',
                                '888888','999999']
                if record.pincode:
                    match_zip_code = re.match('^[\d]*$', record.pincode)
                    if not record.pincode in invalid_pincode_list:
                        if not match_zip_code or len(record.pincode) != 6:
                            state = 'invalid'
            if self.sudo().search_count([('mobile','=',record.mobile),('name','=',record.name),('studying_course_id','=',record.studying_course_id.id)]) > 1:
                state = 'invalid'
            if record.mobile:
                invalid_mobile_numbers = ['0000000000','1111111111','2222222222','3333333333','4444444444','5555555555','6666666666',
                                          '7777777777','8888888888','9999999999']
                match_mobile = re.match('^[\d]*$', record.mobile)
                if not match_mobile or len(record.mobile) != 10 or record.mobile in invalid_mobile_numbers:
                    state = 'invalid'
            return state     
        
    @api.multi
    def validate_record(self):
        for record in self:
            state = 'invalid'
            if record.branch_id and record.employee_id and record.name and record.mobile \
                    and record.studying_course_id and record.state_id and record.district_id:
                state = 'valid'
            else:
                raise ValidationError("Please fill all mandatory fields.")
            if record.name:
                name = self.env['res.company']._validate_name(record.name)
                record.name = name
            if record.pincode:
                invalid_pincode_list = ['000000','111111','222222','333333','444444','555555','666666','777777',
                                '888888','999999']
                if record.pincode:
                    match_zip_code = re.match('^[\d]*$', record.pincode)
                    if not record.pincode in invalid_pincode_list:
                        if not match_zip_code or len(record.pincode) != 6:
                            state = 'invalid'
                            raise ValidationError("Please enter valid pincode.")
            if self.sudo().search_count([('mobile','=',record.mobile),('name','=',record.name),('studying_course_id','=',record.studying_course_id.id)]) > 1:
                state = 'invalid'
                raise ValidationError('Record already exists with given mobile, student name and studying course.')
            if record.mobile:
                invalid_mobile_numbers = ['0000000000','1111111111','2222222222','3333333333','4444444444','5555555555','6666666666',
                                          '7777777777','8888888888','9999999999']
                match_mobile = re.match('^[\d]*$', record.mobile)
                if not match_mobile or len(record.mobile) != 10 or record.mobile in invalid_mobile_numbers:
                    state = 'invalid'
                    raise ValidationError("Please enter valid mobile number.")
            return state    
    
    @api.onchange('branch_id','employee_id')
    def onchange_branch_id(self):
        if not self.employee_id:
            self.branch_id = False
        domain={}; domain['branch_id'] = [('id','in',[])]
        if self.employee_id and self.employee_id.payroll_branch_id:
            branch_ids = self.env['res.company'].search([('tem_state_id','=',self.employee_id.payroll_branch_id.state_id.id)]).ids
            domain['branch_id'] = [('id','in',branch_ids)]
        return {'domain':domain}
    
    @api.model
    def create(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        if not 'payroll_branch_id' in vals and 'employee_id' in vals:
            employee_obj = self.env['hr.employee'].search([('id','=',vals['employee_id'])])
            vals.update({'payroll_branch_id':employee_obj.payroll_branch_id.id if employee_obj.payroll_branch_id else None})
        res = super(pappaya_lead_stud_address, self).create(vals)
        if res:
            res.update({'status':res.default_status()})
        return res

    @api.multi
    def write(self, vals):
        if vals.get('name'):
            vals.update({'name': self.env['res.company']._validate_name(vals.get('name'))})
        if not 'payroll_branch_id' in vals and 'employee_id' in vals:
            employee_obj = self.env['hr.employee'].search([('id','=',vals['employee_id'])])
            vals.update({'payroll_branch_id':employee_obj.payroll_branch_id.id if employee_obj.payroll_branch_id else None})
        return super(pappaya_lead_stud_address, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            name = self.env['res.company']._validate_name(self.name)
            self.name = name
    
    @api.multi
    def unlink(self):
        for record in self:
            if record.status == 'valid':
                raise ValidationError('Sorry,You are not authorized to delete record')
            res = super(pappaya_lead_stud_address, record).unlink()
        return res
    
    # Commented based on change discussion with Anto on 23/10/2018 by lokesh.
#     @api.onchange('pincode')
#     def _onchange_pincode(self):
#         if self.pincode:
#             self.env['res.company'].validate_zip(self.pincode)
    
    @api.constrains('mobile','name','studying_course_id')
    def validate_unique(self):
        if self.sudo().search_count([('mobile','=',self.mobile),('name','=',self.name),('studying_course_id','=',self.studying_course_id.id)]) > 1:
            raise ValidationError("Record already exists with given mobile, student name and studying course.")
    
    @api.onchange('state_id')
    def onchange_state_id(self):
        domain = {}
        domain['state_id'] = [('id','in',[])]
#         domain['school_state_id'] = [('id','in',[])]
        state_ids = self.env['res.country.state'].search([('country_id','in',self.env['res.country'].sudo().search([('is_active','=',True)]).ids)])
        if state_ids:
            domain['state_id'] = [('id','in',state_ids.ids)]
#             domain['school_state_id'] = [('id','in',state_ids.ids)]
        return {'domain':domain}   

    @api.onchange('state_id')
    def _onchange_state_id(self):
        if self.state_id:
            self.district_id = None
            
#     @api.onchange('district_id')
#     def _onchange_district_id(self):
#         if self.district_id:
#             self.city_id = None; self.ward_id = None; self.area_id = None; 
#             self.mandal_id = None; self.village_id = None;
    
#     @api.onchange('city_id')
#     def _onchange_city_id(self):
#         if self.city_id:
#             self.ward_id = None; self.area_id = None; 
    
#     @api.onchange('ward_id')
#     def _onchange_ward_id(self):
#         if self.ward_id:
#             self.area_id = None;
    
#     @api.onchange('mandal_id')
#     def _onchange_mandal_id(self):
#         if self.mandal_id:
#             self.village_id = None;
    # End
    
#     @api.onchange('school_state_id')
#     def _onchange_school_state_id(self):
#         if self.school_state_id:
#             self.school_district_id = None; self.school_mandal_id = None; self.lead_school_id = None
#     
#     @api.onchange('school_district_id')
#     def _onchange_school_district_id(self):
#         if self.school_district_id:
#             self.school_mandal_id = None; self.lead_school_id = None
#     
#     @api.onchange('school_mandal_id')
#     def _onchange_school_mandal_id(self):
#         if self.school_mandal_id:
#             self.lead_school_id = None
                
    # Commented based on change discussion with Anto on 23/10/2018 by lokesh. 
#     @api.onchange('mobile')
#     def _onchange_mobile(self):
#         if self.mobile:
#             self.env['res.company'].validate_mobile(self.mobile)
            
    
    """Address Collection Report Dynamic"""
       
    @api.model
    def address_collection_report(self, report_type, state_ids=[], district_ids=[], branch_ids=[], 
    payroll_branch_ids=[], employee_ids=[], lead_course_ids=[], is_class_wise=False):
        print("\n\nReport Type => ", report_type, "")
        print("State ids => ", state_ids, "\n")
        print("district ids => ", district_ids, "\n")
        print("branch_ids => ", branch_ids, "\n")
        print("payroll_branch_ids => ", payroll_branch_ids, "\n")
        print("employee_ids => ", employee_ids, "\n")
        print("lead_course_ids => ", lead_course_ids, "\n")
        print("Class wise => ", is_class_wise, "\n\n")

        if report_type and report_type == 'branch':
            search_condition = []
            if state_ids:
                search_condition.append(('branch_id.state_id', 'in', state_ids))
            if district_ids:
                search_condition.append(('branch_id.state_district_id', 'in', district_ids))
            if branch_ids:
                search_condition.append(('branch_id', 'in', branch_ids))
            if is_class_wise:
                if lead_course_ids:
                    search_condition.append(('studying_course_id', 'in', lead_course_ids))
            record_branch_ids = self.env['pappaya.lead.stud.address'].search(search_condition).mapped('branch_id').ids; record_branch_ids = set(record_branch_ids)
        
            if record_branch_ids:
                return self.address_collection_branch_wise_report(record_branch_ids, lead_course_ids, is_class_wise)
            
        elif report_type and report_type == 'employee':
            search_condition = []
            if payroll_branch_ids:
                search_condition.append(('employee_id.payroll_branch_id', 'in', payroll_branch_ids))
            if employee_ids:
                search_condition.append(('employee_id', 'in', employee_ids))
            if is_class_wise:
                if lead_course_ids:
                    search_condition.append(('studying_course_id', 'in', lead_course_ids))
            
            record_employee_ids = self.env['pappaya.lead.stud.address'].search(search_condition).mapped('employee_id').ids; record_employee_ids = set(record_employee_ids)
            
            if record_employee_ids:
                return self.address_collection_employee_wise_report(record_employee_ids, lead_course_ids, is_class_wise)
        elif report_type and report_type == 'branch_and_employee':
            search_condition = []
            if state_ids:
                search_condition.append(('branch_id.state_id', 'in', state_ids))
            if district_ids:
                search_condition.append(('branch_id.state_district_id', 'in', district_ids))
            if branch_ids:
                search_condition.append(('branch_id', 'in', branch_ids))    
            if payroll_branch_ids:
                search_condition.append(('employee_id.payroll_branch_id', 'in', payroll_branch_ids))
            if employee_ids:
                search_condition.append(('employee_id', 'in', employee_ids))
            if is_class_wise and lead_course_ids:
                    search_condition.append(('studying_course_id', 'in', lead_course_ids))
            record_employee_ids =  self.env['pappaya.lead.stud.address'].search(search_condition).mapped('employee_id').ids; record_employee_ids = set(record_employee_ids)
            if record_employee_ids:
                return self.address_collection_branch_and_employee_wise_report(record_employee_ids, employee_ids, branch_ids, lead_course_ids, is_class_wise)        
        
    @api.multi
    def address_collection_branch_wise_report(self, record_branch_ids, lead_course_ids, is_class_wise):
        final_result = []
        headers = ['Branch Name']
        unique_classes_list = []
        for record_branch_id in record_branch_ids:
            if lead_course_ids:
                student_addresses = self.env['pappaya.lead.stud.address'].search([('branch_id','=',record_branch_id),('studying_course_id','in',lead_course_ids)])
            else:
                student_addresses = self.env['pappaya.lead.stud.address'].search([('branch_id','=',record_branch_id)])
            result_dict = {}
            result_dict.update({'Branch Name': self.env['res.company'].sudo().search([('id','=',record_branch_id)]).name})
            if is_class_wise:
                for address in student_addresses:
                    if address.studying_course_id.name in result_dict:
                        result_dict[address.studying_course_id.name] += 1
                    else:
                        if not address.studying_course_id.name in unique_classes_list:
                            if re.search(roman_pattern, str(address.studying_course_id.name).upper()):
                                unique_classes_list.append(address.studying_course_id.name)
                            else:
                                if not address.studying_course_id.name in headers:
                                    headers.append(address.studying_course_id.name)
                        result_dict[address.studying_course_id.name] = 1
            result_dict['Total Count'] = len(student_addresses.ids)
            final_result.append(result_dict)
        if is_class_wise:
            headers += sort_roman_letters(unique_classes_list)
        headers.append('Total Count')
        return {'result':final_result,
                'headers':headers}   
                
    @api.multi
    def address_collection_employee_wise_report(self, record_employee_ids, lead_course_ids, is_class_wise):
        final_result = []
        headers = ['Employee Name','Employee ID','Mobile Number']
        unique_classes_list = []
        for employee in record_employee_ids:
            result_dict = {}
            employee_sr = self.env['hr.employee'].sudo().search([('id','=',employee)])
            result_dict.update({'Employee Name':employee_sr.name, 'Employee ID':employee_sr.emp_id, 'Mobile Number':employee_sr.work_mobile})
            if lead_course_ids:
                student_addresses = self.env['pappaya.lead.stud.address'].search([('employee_id','=',employee),('studying_course_id','in',lead_course_ids)])
            else:
                student_addresses = self.env['pappaya.lead.stud.address'].search([('employee_id','=',employee)])
                       
            if is_class_wise:
                for address in student_addresses:
                    if address.studying_course_id.name in result_dict:
                        result_dict[address.studying_course_id.name] += 1
                    else:
                        if not address.studying_course_id.name in unique_classes_list:
                            if re.search(roman_pattern, str(address.studying_course_id.name).upper()):
                                unique_classes_list.append(address.studying_course_id.name)
                            else:
                                if not address.studying_course_id.name in headers:
                                    headers.append(address.studying_course_id.name)
                        result_dict[address.studying_course_id.name] = 1
            result_dict.update({'Total Count':len(student_addresses.ids)})
            final_result.append(result_dict)
        if is_class_wise:
            headers += sort_roman_letters(unique_classes_list)
        headers.append('Total Count')
        return {'result':final_result,
                'headers':headers}
    
    @api.multi
    def address_collection_branch_and_employee_wise_report(self, record_employee_ids, employee_ids, branch_ids, lead_course_ids, is_class_wise):
        final_result = []
        headers = ['Branch Name','Employee Name','Employee ID','Mobile Number']
        unique_classes_list = []
        emp_ids = employee_ids if employee_ids else record_employee_ids
        for employee in emp_ids:
            result_dict = {}
            if lead_course_ids:
                student_addresses = self.env['pappaya.lead.stud.address'].search([('studying_course_id','in',lead_course_ids),('employee_id','=',employee_id)])
            elif branch_ids:
                student_addresses = self.env['pappaya.lead.stud.address'].search([('branch_id','in',branch_ids),('employee_id','=',employee_id)])
            else:
                student_addresses = self.env['pappaya.lead.stud.address'].search([('employee_id','=',employee)])
            for address in student_addresses:
                result_dict.update({'Branch Name': address.branch_id.name,'Employee Name':address.employee_id.name, 'Employee ID':address.employee_id.emp_id, 
                                    'Mobile Number':address.employee_id.work_mobile})    
                if is_class_wise:
                    if address.studying_course_id.name in result_dict:
                        result_dict[address.studying_course_id.name] += 1
                    else:
                        if not address.studying_course_id.name in unique_classes_list:
                            if re.search(roman_pattern, str(address.studying_course_id.name).upper()):
                                unique_classes_list.append(address.studying_course_id.name)
                            else:
                                if not address.studying_course_id.name in headers:
                                    headers.append(address.studying_course_id.name)
                        result_dict[address.studying_course_id.name] = 1
            result_dict['Total Count'] = len(student_addresses.ids)
            final_result.append(result_dict)
        if is_class_wise:
            headers += sort_roman_letters(unique_classes_list)
        headers.append('Total Count')
        return {'result':final_result,
                'headers':headers}            
