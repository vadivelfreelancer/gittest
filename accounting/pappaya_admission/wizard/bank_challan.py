from odoo import models, fields, api
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError


class BankChallan(models.TransientModel):
    _name = 'bank.challan'

    branch_id = fields.Many2one('operating.unit', string='Branch')
    application_no = fields.Char('Admission/Reservation No')
    std_type = fields.Selection([('admission', 'Admission'), ('reservation', 'Reservation')], string='Business Stage',store=True)
    ad_date = fields.Date('Date')
    branch = fields.Char('Branch')
    num = fields.Char('Admission/Reservation No')
    code = fields.Char('Code')
    name = fields.Char('Student Name')
    father_name = fields.Char('Father Name')

    @api.onchange('application_no')
    def _onchange_application(self):
        if self.application_no:
            addmition_obj = self.env['pappaya.admission'].search([('res_no', '=', self.application_no), ('branch_id', '=', self.branch_id.id)])
            for val in addmition_obj:
                if val.is_res_stage == True:
                   self.update({'std_type':'reservation'})
                else:
                    self.update({'std_type': 'admission'})


    @api.onchange('branch_id','application_no','std_type')
    def _onchange_application_no(self):
        if self.application_no and self.branch_id and self.std_type:
            stud_obj=self.env['res.partner'].search([('admission_no','=',self.application_no),('school_id','=',self.branch_id.id)])
            if not stud_obj:
                raise ValidationError('This Information Not Matching With Any Students')
            if stud_obj:
                self.update({'num':stud_obj.admission_no,
                                     'ad_date':stud_obj.date_of_joining,
                                     'branch':stud_obj.school_id.name,
                                     'code':stud_obj.course_package_id.name,
                                     'name':stud_obj.name,
                                     'father_name':stud_obj.father_name
                                     })


    @api.multi
    def print_challan_student(self):
        return self.env.ref('pappaya_admission.bank_challan_reports_id').get_report_action(self)

    @api.multi
    def get_challan_report_data(self):
        stud_obj=[]
        if self.application_no and self.branch_id:
            stud_obj=self.env['res.partner'].search([('admission_no','=',self.application_no),('school_id','=',self.branch_id.id)])
        return stud_obj

    @api.multi
    def get_challan_report_reservation(self):
        data_list = []
        if self.application_no:
            addmition_obj = self.env['pappaya.admission'].search([('res_no', '=', self.application_no),('branch_id','=',self.branch_id.id)])
            for val in addmition_obj:
                if val.is_res_stage==True:
                    stage = True
                    vals = {}
                    vals['res_stage'] = stage
                    data_list.append(vals)
        return data_list



