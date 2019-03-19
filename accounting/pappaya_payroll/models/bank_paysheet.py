import time
from datetime import datetime
from dateutil import relativedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError
import babel
import xlsxwriter
import base64
import csv
import os
import xlwt
from io import BytesIO
from xlwt import *
import dateutil.parser

    
class BankPaySheet(models.Model):
    _name = 'pappaya.bank.paysheet'
    _inherit = 'mail.thread'
    _order = "id desc"
    _rec_name = 'bank_id'

    bank_id = fields.Many2one('res.bank', string="Bank")
    date_start = fields.Date(string='Date From',default=lambda *a: time.strftime('%Y-%m-01'))
    date_end = fields.Date(string='Date To',default=lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    region_id = fields.Many2one('pappaya.region')
    state_id = fields.Many2one('res.country.state',domain=[('country_id.is_active','=',True)])
    district_id = fields.Many2one('state.district')
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    department_id = fields.Many2one('hr.department')
    designation_id = fields.Many2one('hr.job')
    entity_id = fields.Many2one('operating.unit', 'Entity', domain=[('type', '=', 'entity')])
    salary_range = fields.Float('Salary Range')
    operators = fields.Selection([('=','='),('!=','!='),('>','>'),('>=','>='),('<','<'),('<=','<=')])
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string="Status", default='draft', track_visibility='onchange', copy=False)
    paysheet_line = fields.One2many('pappaya.bank.paysheet.line','bank_paysheet_id', string='Paysheet Lines')

    @api.constrains('date_start','date_end')
    def check_from_to_date(self):
        for record in self:
            if record.date_start and record.date_end:
                from_date = dateutil.parser.parse(record.date_start).date()
                if from_date > datetime.today().date():
                    raise ValidationError(_("From Date must be less than or equal to Current Date"))
                to_date = dateutil.parser.parse(record.date_end).date()
                if to_date < from_date:
                    raise ValidationError(_("To Date must be greater than Start Date"))

    @api.constrains('salary_range')
    def check_salary_range(self):
        for record in self:
            if record.salary_range and record.salary_range < 0:
                raise ValidationError("Salary Range should not be Negative")

    @api.onchange('region_id')
    def onchange_region_id(self):
        for record in self:
            entity_domain = []
            branch_domain = []
            region_domain = []
            if record.region_id:
                branch_domain.append(('region_id', '=', record.region_id.id))
                region_domain.append(('id', 'in', record.region_id.state_id.ids))
            if record.district_id:
                entity_domain.append(('tem_district_id', '=', record.district_id.id))
                branch_domain.append(('district_id', '=', record.district_id.id))
            if record.state_id:
                entity_domain.append(('tem_state_id', '=', record.state_id.id))
                branch_domain.append(('state_id', '=', record.state_id.id))
            entity_domain.append(('type', '=', 'entity'))
            branch_domain.append(('type', '=', 'branch'))
            record.state_id = record.district_id = record.entity_id = record.branch_id = None
            return {'domain': {'state_id': region_domain, 'entity_id': entity_domain, 'branch_id': branch_domain}}

    @api.onchange('state_id')
    def onchange_state_id(self):
        for record in self:
            entity_domain = []
            branch_domain = []
            state_domain = []
            if record.region_id:
                branch_domain.append(('region_id', '=', record.region_id.id))
            if record.district_id:
                entity_domain.append(('tem_district_id', '=', record.district_id.id))
                branch_domain.append(('district_id', '=', record.district_id.id))
            if record.state_id:
                entity_domain.append(('tem_state_id', '=', record.state_id.id))
                branch_domain.append(('state_id', '=', record.state_id.id))
                state_domain.append(('state_id', '=', record.state_id.id))
            entity_domain.append(('type', '=', 'entity'))
            branch_domain.append(('type', '=', 'branch'))
            record.district_id = record.entity_id = record.branch_id = None
            return {'domain': {'district_id': state_domain, 'entity_id': entity_domain, 'branch_id': branch_domain}}

    @api.onchange('district_id')
    def onchange_district_id(self):
        for record in self:
            entity_domain = []
            branch_domain = []
            if record.state_id:
                entity_domain.append(('tem_state_id', '=', record.state_id.id))
                branch_domain.append(('state_id', '=', record.state_id.id))
            if record.region_id:
                branch_domain.append(('region_id', '=', record.region_id.id))
            if record.district_id:
                entity_domain.append(('tem_district_id', '=', record.district_id.id))
                branch_domain.append(('district_id', '=', record.district_id.id))
            entity_domain.append(('type', '=', 'entity'))
            branch_domain.append(('type', '=', 'branch'))
            record.entity_id = record.branch_id = None
            return {'domain': { 'entity_id': entity_domain, 'branch_id': branch_domain}}

    @api.onchange('entity_id')
    def onchange_entity_id(self):
        for record in self:
            domain = []
            if record.entity_id:
                domain.append(('parent_id', '=', record.entity_id.id))
            record.branch_id = record.department_id = record.designation_id = None
            return {'domain': {'branch_id': domain}}

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        for record in self:
            job_positions = self.env['hr.job'].search([('office_type_id', '=', record.branch_id.office_type_id.id)])
            department = []
            for job in job_positions:
                department.append(job.department_id.id)
            record.department_id = record.designation_id = None
            return {'domain': {'department_id': [('id','in',department)]}}

    @api.onchange('department_id')
    def onchange_department_id(self):
        for record in self:
            domain = []
            if record.department_id:
                domain.append(('department_id', '=', record.department_id.id))
            record.designation_id = None
            return {'domain': {'designation_id': domain}}
    

    @api.multi
    def action_reset(self):
        for record in self:
            record.state = 'draft'
                            
    @api.multi
    def action_done(self):
        for record in self:
            record.state = 'done'

    @api.multi
    def generate_paysheet(self):
        workbook = xlwt.Workbook()
        company_name = xlwt.easyxf('font: name Times New Roman, height 350, bold on; align: wrap on, vert centre, horiz centre;')
        company_address = xlwt.easyxf('font: name Times New Roman, height 230, bold on; align: wrap on, vert centre, horiz centre;')
        header = xlwt.easyxf('font: name Times New Roman, height 200, bold on,italic off; align: wrap on, vert centre, horiz centre;  borders: top thin, bottom thin, left thin, right thin;')
        answer = xlwt.easyxf('font: name Times New Roman, height 200; borders: top thin, bottom thin, left thin, right thin;')

        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy hh:mm:ss'

        sheet_name = 'Bank Pay Sheet'
        sheet = workbook.add_sheet(sheet_name)
        sheet.row(0).height = 450;

        style_header_without_border = XFStyle()
        fnt = Font()
        fnt.bold = True
        fnt.height = 12 * 0x14
        style_header_without_border.font = fnt
        al1 = Alignment()
        al1.horz = Alignment.HORZ_CENTER
        al1.vert = Alignment.VERT_CENTER
        pat2 = Pattern()
        style_header_without_border.alignment = al1
        style_header_without_border.pattern = pat2

        style_center_align_without_border = XFStyle()
        al_c = Alignment()
        al_c.horz = Alignment.HORZ_CENTER
        al_c.vert = Alignment.VERT_CENTER
        style_center_align_without_border.alignment = al_c

        row_no = 1;
        sheet.row(1).height = 350;

        sheet.col(0).width = 256 * 20; sheet.col(1).width = 256 * 20; sheet.col(2).width = 256 * 20; sheet.col(3).width = 256 * 20;
        sheet.col(4).width = 256 * 20; sheet.col(5).width = 256 * 20; sheet.col(6).width = 256 * 14; sheet.col(7).width = 256 * 14;
        sheet.col(8).width = 256 * 20; sheet.col(9).width = 256 * 20; sheet.col(10).width = 256 * 40; sheet.col(11).width = 256 * 20;
        sheet.col(12).width = 256 * 30; sheet.col(13).width = 256 * 20; sheet.col(14).width = 256 * 15; sheet.col(15).width = 256 * 15;
        sheet.col(16).width = 256 * 20; sheet.col(17).width = 256 * 25; sheet.col(18).width = 256 * 25; sheet.col(19).width = 256 * 25;
        sheet.col(20).width = 256 * 25; sheet.col(21).width = 256 * 25; sheet.col(22).width = 256 * 20; sheet.col(23).width = 256 * 20;
        sheet.col(24).width = 256 * 20; sheet.col(25).width = 256 * 20; sheet.col(26).width = 256 * 20; sheet.col(27).width = 256 * 20;
        sheet.col(28).width = 256 * 20; sheet.col(29).width = 256 * 20; sheet.col(30).width = 256 * 20; sheet.col(31).width = 256 * 20;
        sheet.col(32).width = 256 * 20; sheet.col(33).width = 256 * 20; sheet.col(34).width = 256 * 20; sheet.col(35).width = 256 * 20;
        sheet.col(36).width = 256 * 20; sheet.col(37).width = 256 * 20; sheet.col(38).width = 256 * 20; sheet.col(39).width = 256 * 20;
        sheet.col(40).width = 256 * 20; sheet.col(41).width = 256 * 20; sheet.col(42).width = 256 * 20; sheet.col(43).width = 256 * 20;
        sheet.col(44).width = 256 * 20; sheet.col(45).width = 256 * 20; sheet.col(46).width = 256 * 20; sheet.col(47).width = 256 * 20; sheet.col(48).width = 256 * 20;
 
        sheet.write(row_no, 0, "Client_Code", header); sheet.write(row_no, 1, "Product_Code", header); sheet.write(row_no, 2, "Payment_Type", header); sheet.write(row_no, 3, "Payment Ref No", header);
        sheet.write(row_no, 4, "Payment_Date", header); sheet.write(row_no, 5, "Instrument Date", header); sheet.write(row_no, 6, "Dr_Ac_No", header); sheet.write(row_no, 7, "Amount", header);
        sheet.write(row_no, 8, "Bank_Code_Indicator", header); sheet.write(row_no, 9, "Beneficiary_Code", header); sheet.write(row_no, 10, "Beneficiary_Name", header);sheet.write(row_no, 11, "Beneficiary_Bank", header);
        sheet.write(row_no, 12, "Beneficiary_Branch / IFSC Code", header); sheet.write(row_no, 13, "Beneficiary_Acc_No", header); sheet.write(row_no, 14, "Location", header); sheet.write(row_no, 15, "Print_Location", header);
        sheet.write(row_no, 16, "Instrument_Number", header); sheet.write(row_no, 17, "Ben_Add1", header); sheet.write(row_no, 18, "Ben_Add2", header); sheet.write(row_no, 19, "Ben_Add3", header);
        sheet.write(row_no, 20, "Ben_Add4", header); sheet.write(row_no, 21, "Beneficiary_Email", header); sheet.write(row_no, 22, "Beneficiary_Mobile", header); sheet.write(row_no, 23, "Debit_Narration", header);
        sheet.write(row_no, 24, "Credit_Narration", header); sheet.write(row_no, 25, "Payment Details 1", header); sheet.write(row_no, 26, "Payment Details 2", header); sheet.write(row_no, 27, "Payment Details 3", header);
        sheet.write(row_no, 28, "Payment Details 4", header); sheet.write(row_no, 29, "Enrichment_1", header); sheet.write(row_no, 30, "Enrichment_2", header); sheet.write(row_no, 31, "Enrichment_3", header);
        sheet.write(row_no, 32, "Enrichment_4", header); sheet.write(row_no, 33, "Enrichment_5", header); sheet.write(row_no, 34, "Enrichment_6", header); sheet.write(row_no, 35, "Enrichment_7", header);
        sheet.write(row_no, 36, "Enrichment_8", header); sheet.write(row_no, 37, "Enrichment_9", header); sheet.write(row_no, 38, "Enrichment_10", header); sheet.write(row_no, 39, "Enrichment_11", header);
        sheet.write(row_no, 40, "Enrichment_12", header); sheet.write(row_no, 41, "Enrichment_13", header); sheet.write(row_no, 42, "Enrichment_14", header); sheet.write(row_no, 43, "Enrichment_15", header);
        sheet.write(row_no, 44, "Enrichment_16", header); sheet.write(row_no, 45, "Enrichment_17", header); sheet.write(row_no, 46, "Enrichment_18", header); sheet.write(row_no, 47, "Enrichment_19", header); sheet.write(row_no, 48, "Enrichment_20", header)

        if self.date_start and self.date_end and self.bank_id:

            domain = []
            if self.state_id:
                domain.append(('state_id', '=', self.state_id.id))
            if self.region_id:
                domain.append(('region_id', '=', self.region_id.id))
            if self.district_id:
                domain.append(('district_id', '=', self.district_id.id))
            if self.entity_id:
                domain.append(('parent_id', '=', self.entity_id.id))
            if self.branch_id:
                domain.append(('id', '=', self.branch_id.id))

            domain.append(('type', '=', 'branch'))

            branch_sr = self.env['operating.unit'].search(domain)

            payslip_domain = []
            if self.state_id or self.region_id or self.district_id or self.entity_id or self.branch_id:
                payslip_domain.append(('branch_id', 'in', branch_sr.ids))
            if self.department_id:
                payslip_domain.append(('employee_id.department_id', '=', self.department_id.id))
            if self.designation_id:
                payslip_domain.append(('employee_id.job_id', '=', self.designation_id.id))
            if self.date_start:
                payslip_domain.append(('date_from', '=', self.date_start))
            if self.date_end:
                payslip_domain.append(('date_to', '=', self.date_end))
            if self.bank_id:
                payslip_domain.append(('payslip_bank_id', 'in', (self.bank_id.id,False)))

            payslip_domain.append(('state', '=', 'done'))
            payslip_domain.append(('is_paysheet_created', '=', False))

            payslip_value = self.env['hr.payslip'].search(payslip_domain, order="branch_id")
            
            if self.operators and self.salary_range:
                    slip_ids = []
                    for line in self.env['hr.payslip.line'].search([('slip_id','in',payslip_value.ids),('code','=','NET'),('amount',self.operators,self.salary_range)]):
                        slip_ids.append(line.slip_id.id)
                    payslip_value = self.env['hr.payslip'].search([('id','in',slip_ids)],order="branch_id")

            if not payslip_value:
                raise ValidationError(_("No Records found to generate Bank Paysheet"))

            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(self.date_start, "%Y-%m-%d")))
            locale = self.env.context.get('lang') or 'en_US'
            month_name = tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))

            title = self.bank_id.name + '  ' + month_name

            sheet.write_merge(0, 0, 0, 8, title , company_address)
            row_no += 1
            for payslip in payslip_value:
                sheet.write(row_no, 0, None, answer); sheet.write(row_no, 1, None, answer); sheet.write(row_no, 2, None, answer); sheet.write(row_no, 3, None, answer);
                sheet.write(row_no, 4, None, answer); sheet.write(row_no, 5, None, answer); sheet.write(row_no, 6, None, answer); sheet.write(row_no, 7, '%.2f' % payslip.net_amount, answer);
                sheet.write(row_no, 8, None, answer); sheet.write(row_no, 9, None, answer); sheet.write(row_no, 10, payslip.employee_id.name, answer); sheet.write(row_no, 11, payslip.employee_id.bank_id.name, answer);
                sheet.write(row_no, 12, payslip.employee_id.ifsc, answer); sheet.write(row_no, 13, payslip.employee_id.account_number, answer); sheet.write(row_no, 14, None, answer); sheet.write(row_no, 15, None, answer);
                sheet.write(row_no, 16, None, answer); sheet.write(row_no, 17, None, answer); sheet.write(row_no, 18, None, answer); sheet.write(row_no, 19, None, answer);
                sheet.write(row_no, 20, None, answer); sheet.write(row_no, 21, payslip.employee_id.work_email, answer); sheet.write(row_no, 22, payslip.employee_id.work_mobile, answer); sheet.write(row_no, 23, None, answer);
                sheet.write(row_no, 24, None, answer); sheet.write(row_no, 25, None, answer); sheet.write(row_no, 26, None, answer); sheet.write(row_no, 27, None, answer);
                sheet.write(row_no, 28, None, answer); sheet.write(row_no, 29, None, answer); sheet.write(row_no, 30, None, answer); sheet.write(row_no, 31, None, answer);
                sheet.write(row_no, 32, None, answer); sheet.write(row_no, 33, None, answer); sheet.write(row_no, 34, None, answer); sheet.write(row_no, 35, None, answer);
                sheet.write(row_no, 36, None, answer); sheet.write(row_no, 37, None, answer); sheet.write(row_no, 38, None, answer); sheet.write(row_no, 39, None, answer);
                sheet.write(row_no, 40, None, answer); sheet.write(row_no, 41, None, answer); sheet.write(row_no, 42, None, answer); sheet.write(row_no, 43, None, answer);
                sheet.write(row_no, 44, None, answer); sheet.write(row_no, 45, None, answer); sheet.write(row_no, 46, None, answer); sheet.write(row_no, 47, None, answer); sheet.write(row_no, 48, None, answer)

                payslip.payslip_bank_id = self.bank_id
                payslip.is_paysheet_created = True

                row_no += 1

            row_no += 1

            date_value = time.strftime('%d-%m-%Y %H:%M:%S')
            footer = 'Generated By' + ' : ' + self.env.user.partner_id.name + '    ' + 'Dated on' + ' : ' + date_value
            sheet.write_merge(row_no, row_no, 0, 8, footer, answer)

            # sheet.write(row_no, 0, 'Generated By', answer); sheet.write(row_no, 1, self.env.user.partner_id.name, answer);
            # sheet.write(row_no, 2, 'Dated on', answer); sheet.write(row_no, 3, datetime.now(), date_format);

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()

        data = base64.encodebytes(data)

        sequence_no = self.env['ir.sequence'].next_by_code('bank.paysheet') or _('New')

        self.write({
            'paysheet_line':[(0, 0, {'bank_paysheet_id':self.id, 'sequence_no':sequence_no, 'dated_on':datetime.now(), 'generated_by':self.env.user.id, 'filedata': data, 'filename': 'Bank Pay Sheet.xls'})]
        })


        # url = os.path.dirname(os.path.realpath('pappaya_payroll'))
        # cwd = os.path.abspath(__file__)
        # path = cwd.rsplit('/', 2)
        # url = path[0] + '/report_templates'
        #
        # workbook = xlsxwriter.Workbook(url+ '/' + 'Bank Pay Sheet.xls')
        # worksheet = workbook.add_worksheet()
        #
        # # creation of header
        # merge_format = workbook.add_format(
        #     {'bold': 1, 'border': 1, 'font_size': 11, 'align': 'center', 'valign': 'vcenter', 'fg_color': 'white'})
        # merge_format1 = workbook.add_format(
        #     {'bold': 1, 'border': 1, 'align': 'center', 'font_size': 11, 'valign': 'vcenter'})
        # merge_format2 = workbook.add_format(
        #     {'bold': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'border': 1, 'fg_color': 'gray',
        #      'num_format': '#,##0,0.00', })
        # merge_format4 = workbook.add_format(
        #     {'align': 'center', 'font_size': 11, 'valign': 'vcenter', 'num_format': '#,##0,0.00', })
        #
        #
        # worksheet.set_column('A:A', 20); worksheet.set_column('B:B', 20); worksheet.set_column('C:C', 20); worksheet.set_column('D:D', 20);
        # worksheet.set_column('E:E', 20); worksheet.set_column('F:F', 20); worksheet.set_column('G:G', 14); worksheet.set_column('H:H', 14);
        # worksheet.set_column('I:I', 20); worksheet.set_column('J:J', 20); worksheet.set_column('K:K', 40); worksheet.set_column('L:L', 20);
        # worksheet.set_column('M:M', 30); worksheet.set_column('N:N', 20); worksheet.set_column('O:O', 15); worksheet.set_column('P:P', 15);
        # worksheet.set_column('Q:Q', 20); worksheet.set_column('R:R', 25); worksheet.set_column('S:S', 25); worksheet.set_column('T:T', 25);
        # worksheet.set_column('U:U', 25); worksheet.set_column('V:V', 25); worksheet.set_column('W:W', 20); worksheet.set_column('X:X', 20);
        # worksheet.set_column('Y:Y', 20); worksheet.set_column('Z:Z', 20); worksheet.set_column('AA:AA', 20); worksheet.set_column('AB:AB', 20);
        # worksheet.set_column('AC:AC', 20); worksheet.set_column('AD:AD', 20); worksheet.set_column('AE:AE', 20); worksheet.set_column('AF:AF', 20);
        # worksheet.set_column('AG:AG', 20); worksheet.set_column('AH:AH', 20); worksheet.set_column('AI:AI', 20); worksheet.set_column('AJ:AJ', 20);
        # worksheet.set_column('AK:AK', 20); worksheet.set_column('AL:AL', 20); worksheet.set_column('AM:AM', 20); worksheet.set_column('AN:AN', 20);
        # worksheet.set_column('AO:AO', 20); worksheet.set_column('AP:AP', 20); worksheet.set_column('AQ:AQ', 20); worksheet.set_column('AR:AR', 20);
        # worksheet.set_column('AS:AS', 20); worksheet.set_column('AT:AT', 20); worksheet.set_column('AU:AU', 20); worksheet.set_column('AV:AV', 20); worksheet.set_column('AW:AW', 20)
        #
        # worksheet.write('A1', "Client_Code", merge_format1); worksheet.write('B1', "Product_Code", merge_format1); worksheet.write('C1', "Payment_Type", merge_format1); worksheet.write('D1', "Payment Ref No", merge_format1);
        # worksheet.write('E1', "Payment_Date", merge_format1); worksheet.write('F1', "Instrument Date", merge_format1); worksheet.write('G1', "Dr_Ac_No", merge_format1); worksheet.write('H1', "Amount", merge_format1);
        # worksheet.write('I1', "Bank_Code_Indicator", merge_format1); worksheet.write('J1', "Beneficiary_Code", merge_format1); worksheet.write('K1', "Beneficiary_Name", merge_format1);worksheet.write('L1', "Beneficiary_Bank", merge_format1);
        # worksheet.write('M1', "Beneficiary_Branch / IFSC Code", merge_format1); worksheet.write('N1', "Beneficiary_Acc_No", merge_format1); worksheet.write('O1', "Location", merge_format1); worksheet.write('P1', "Print_Location", merge_format1);
        # worksheet.write('Q1', "Instrument_Number", merge_format1); worksheet.write('R1', "Ben_Add1", merge_format1); worksheet.write('S1', "Ben_Add2", merge_format1); worksheet.write('T1', "Ben_Add3", merge_format1);
        # worksheet.write('U1', "Ben_Add4", merge_format1); worksheet.write('V1', "Beneficiary_Email", merge_format1); worksheet.write('W1', "Beneficiary_Mobile", merge_format1); worksheet.write('X1', "Debit_Narration", merge_format1);
        # worksheet.write('Y1', "Credit_Narration", merge_format1); worksheet.write('Z1', "Payment Details 1", merge_format1); worksheet.write('AA1', "Payment Details 2", merge_format1); worksheet.write('AB1', "Payment Details 3", merge_format1);
        # worksheet.write('AC1', "Payment Details 4", merge_format1); worksheet.write('AD1', "Enrichment_1", merge_format1); worksheet.write('AE1', "Enrichment_2", merge_format1); worksheet.write('AF1', "Enrichment_3", merge_format1);
        # worksheet.write('AG1', "Enrichment_4", merge_format1); worksheet.write('AH1', "Enrichment_5", merge_format1); worksheet.write('AI1', "Enrichment_6", merge_format1); worksheet.write('AJ1', "Enrichment_7", merge_format1);
        # worksheet.write('AK1', "Enrichment_8", merge_format1); worksheet.write('AL1', "Enrichment_9", merge_format1); worksheet.write('AM1', "Enrichment_10", merge_format1); worksheet.write('AN1', "Enrichment_11", merge_format1);
        # worksheet.write('AO1', "Enrichment_12", merge_format1); worksheet.write('AP1', "Enrichment_13", merge_format1); worksheet.write('AQ1', "Enrichment_14", merge_format1); worksheet.write('AR1', "Enrichment_15", merge_format1);
        # worksheet.write('AS1', "Enrichment_16", merge_format1); worksheet.write('AT1', "Enrichment_17", merge_format1); worksheet.write('AU1', "Enrichment_18", merge_format1); worksheet.write('AV1', "Enrichment_19", merge_format1); worksheet.write('AW1', "Enrichment_20", merge_format1)
        #
        # if self.date_start and self.date_end and self.bank_id:
        #
        #     domain = []
        #     if self.state_id:
        #         domain.append(('state_id','=',self.state_id.id))
        #     if self.region_id:
        #         domain.append(('region_id','=',self.region_id.id))
        #     if self.district_id:
        #         domain.append(('district_id','=',self.district_id.id))
        #     if self.branch_id:
        #         domain.append(('id','=',self.branch_id.id))
        #
        #     domain.append(('type','=','branch'))
        #
        #     branch_sr = self.env['operating.unit'].search(domain)
        #
        #     payslip_domain = []
        #     if self.state_id or self.region_id or self.district_id or self.branch_id:
        #         payslip_domain.append(('branch_id','in',branch_sr.ids))
        #     if self.department_id:
        #         payslip_domain.append(('employee_id.department_id','=',self.department_id.id))
        #     if self.designation_id:
        #         payslip_domain.append(('employee_id.job_id','=',self.designation_id.id))
        #     if self.date_start:
        #         payslip_domain.append(('date_from','=',self.date_start))
        #     if self.date_end:
        #         payslip_domain.append(('date_to','=',self.date_end))
        #     if self.bank_id:
        #         payslip_domain.append(('employee_id.bank_id','=',self.bank_id.id))
        #     if self.operators and self.salary_range:
        #         payslip_domain.append(('line_ids.code','=','NET'))
        #         payslip_domain.append(('line_ids.amount',self.operators,self.salary_range))
        #
        #     payslip_domain.append(('state','=','done'))
        #
        #     payslip_value = self.env['hr.payslip'].search(payslip_domain,order="branch_id")

        # n = 2
        # for payslip in payslip_value:
        #     worksheet.write('A' + str(n), None, merge_format4); worksheet.write('B' + str(n), None, merge_format4); worksheet.write('C' + str(n), None, merge_format4);
        #     worksheet.write('D' + str(n), None, merge_format4); worksheet.write('E' + str(n), None, merge_format4); worksheet.write('F' + str(n), None, merge_format4);
        #     worksheet.write('G' + str(n), None, merge_format4); worksheet.write('H' + str(n), payslip.net_amount, merge_format4); worksheet.write('I' + str(n), None, merge_format4);
        #     worksheet.write('J' + str(n), None, merge_format4); worksheet.write('K' + str(n), payslip.employee_id.name, merge_format4); worksheet.write('L' + str(n), payslip.employee_id.bank_id.name, merge_format4);
        #     worksheet.write('M' + str(n), payslip.employee_id.ifsc, merge_format4); worksheet.write('N' + str(n), payslip.employee_id.account_number, merge_format4); worksheet.write('O' + str(n), None, merge_format4);
        #     worksheet.write('P' + str(n), None, merge_format4); worksheet.write('Q' + str(n), None, merge_format4); worksheet.write('R' + str(n), None, merge_format4);
        #     worksheet.write('S' + str(n), None, merge_format4); worksheet.write('T' + str(n), None, merge_format4); worksheet.write('U' + str(n), None, merge_format4);
        #     worksheet.write('V' + str(n), payslip.employee_id.work_email, merge_format4); worksheet.write('W' + str(n), payslip.employee_id.work_mobile, merge_format4); worksheet.write('X' + str(n), None, merge_format4);
        #     worksheet.write('Y' + str(n), None, merge_format4); worksheet.write('Z' + str(n), None, merge_format4); worksheet.write('AA' + str(n), None, merge_format4);
        #     worksheet.write('AB' + str(n), None, merge_format4); worksheet.write('AC' + str(n), None, merge_format4); worksheet.write('AD' + str(n), None, merge_format4);
        #     worksheet.write('AE' + str(n), None, merge_format4); worksheet.write('AF' + str(n), None, merge_format4); worksheet.write('AG' + str(n), None, merge_format4);
        #     worksheet.write('AH' + str(n), None, merge_format4); worksheet.write('AI' + str(n), None, merge_format4); worksheet.write('AJ' + str(n), None, merge_format4);
        #     worksheet.write('AK' + str(n), None, merge_format4); worksheet.write('AL' + str(n), None, merge_format4); worksheet.write('AM' + str(n), None, merge_format4);
        #     worksheet.write('AN' + str(n), None, merge_format4); worksheet.write('AO' + str(n), None, merge_format4); worksheet.write('AP' + str(n), None, merge_format4);
        #     worksheet.write('AQ' + str(n), None, merge_format4); worksheet.write('AR' + str(n), None, merge_format4); worksheet.write('AS' + str(n), None, merge_format4);
        #     worksheet.write('AT' + str(n), None, merge_format4); worksheet.write('AU' + str(n), None, merge_format4); worksheet.write('AV' + str(n), None, merge_format4); worksheet.write('AW' + str(n), None, merge_format4)
        #     n = n + 1
        #
        # workbook.close()
        # fo = open(url  + '/' + 'Bank Pay Sheet.xls', "rb+")
        # data = fo.read()
        # out = base64.encodebytes(data)
        # self.write({
        #     'paysheet_line':[(0, 0, {'bank_paysheet_id':self.id, 'dated_on':datetime.now(), 'generated_by':self.env.user.id, 'filedata': out, 'filename': 'Bank Pay Sheet.xls'})]
        # })


class PaymentPaysheetLine(models.Model):
    _name = 'pappaya.bank.paysheet.line'

    bank_paysheet_id = fields.Many2one('pappaya.bank.paysheet')
    sequence_no = fields.Char('Sequence')
    dated_on = fields.Datetime('Dated on')
    generated_by = fields.Many2one('res.users', string='Generated By')
    filedata = fields.Binary('Paysheet file', readonly=True)
    filename = fields.Char('Filename', size=64, readonly=True)