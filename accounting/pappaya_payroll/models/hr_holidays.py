import logging
import math
import calendar
from datetime import datetime, date,timedelta
from werkzeug import url_encode
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo import tools
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil import parser
import threading
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)
HOURS_PER_DAY = 8

class HrHolidaysStatus(models.Model):
    _inherit = 'hr.holidays.status'
    
    entity_id = fields.Many2one('operating.unit', 'Entity',domain=[('type','=','entity')])
    office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    name = fields.Char('Leave Type', required=True, translate=True,size=30)
    #leave_configuration = fields.One2many('hr.holidays.status.line.config','status_id', 'Configurations')
    code = fields.Char(size=5,string='Code')
    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    
    #years_service_from = fields.Integer('Years of Service From')
    years_service = fields.Integer('Years of Service')
    operators = fields.Selection([('=','='),('!=','!='),('>','>'),('>=','>='),('<','<'),('<=','<=')])
    
    max_allowed_days = fields.Float('Max Allowed Days')
    per_month_days = fields.Float('Per Month')
    accrued_leaves  = fields.Float('Accrued Leaves Per Month')
    
    carry_forward = fields.Selection([('yes','Yes'),('no','No')])
    carry_forward_type = fields.Selection([('Balanced','Balance'),('manual','Manual')])
    max_carry_days = fields.Float('Max Carry Forward Days')
    
    leave_encashment = fields.Selection([('yes','Yes'),('no','No')],string='Leave Encashment')
    leave_encashment_type = fields.Selection([('Balanced','Balance'),('manual','Manual')])
    max_leave_encashment_days = fields.Float('Max Leave Encashment Days')
    
    include_all = fields.Boolean(string='Weekly off / Holiday',default=True)
    parts_of_the_day = fields.Selection([('half_day','Half-Day'),('full_day','Full-Day'),('half_full_day','Half-Day or Full-Day')],default='half_full_day')
    work_days = fields.Float(string='Work Days Completed')
    gender = fields.Selection([('male','Male'),('female','Female'),('all','All')],string='Gender',default='all')
    leave_auto_allocation = fields.Boolean(string='Leave Auto Allocation')

    @api.onchange('entity_id')
    def onchange_entity_id(self):
        for record in self:
            record.office_type_id = None

    
    @api.constrains('work_days')
    def check_work_days(self):
        for record in self:
            if record.work_days and record.work_days > 366:
                raise ValidationError("Work Days Completed Range 366 or less days only")
            if record.work_days and record.work_days < 0:
                raise ValidationError('Work Days Completed should not be Negative')
    
    
    @api.constrains('per_month_days')
    def check_per_month_days(self):
        for record in self:
            if record.per_month_days > record.max_allowed_days:
                raise ValidationError("Per month is greater than Max. Allowed Days")
            
            
    @api.multi
    def name_get(self):
        if not self._context.get('employee_id'):
            # leave counts is based on employee_id, would be inaccurate if not based on correct employee
            return super(HrHolidaysStatus, self).name_get()
        res = []
        for record in self:
            name = record.name
            res.append((record.id, name))
        return res

#     @api.constrains('code')
#     def check_code_warning(self):
#         for record in self:
#             if len(record.search([('code','=', record.code)])) > 1:
#                 raise ValidationError(_("Code %s is already exists") % record.code)

    @api.constrains('years_service', 'max_allowed_days', 'per_month_days', 'max_carry_days', 'max_leave_encashment_days')
    def check_negatives(self):
        for record in self:
            is_valid = True
            if self.years_service and self.years_service < 0:
                is_valid = False
            if self.max_allowed_days and self.max_allowed_days < 0:
                is_valid = False
            if self.per_month_days and self.per_month_days < 0:
                is_valid = False
            if self.max_carry_days and self.max_carry_days < 0:
                is_valid = False
            if self.max_leave_encashment_days and self.max_leave_encashment_days < 0:
                is_valid = False

            if not is_valid:
                raise ValidationError("Please check all the values are not in negative values.")
        

# #     
# class HrHolidaysStatusLineConfig(models.Model):
#     _name = 'hr.holidays.status.line.config'
#      
#     status_id = fields.Many2one('hr.holidays.status', 'Status')
#     years_service_from = fields.Integer('Years of Service From')
#     years_service_to = fields.Integer('Years of Service To')
#     max_allowed_days = fields.Integer('Max Allowed Days')
#     per_month_days = fields.Integer('Per Month')
#     max_carry_days = fields.Integer('Max Carry Forward Days')
#     leave_encashment = fields.Boolean('Leave Encashment')


class HrHolidays(models.Model):
    _inherit = "hr.holidays"
    
    office_type_id = fields.Many2one('pappaya.office.type', string="Office Type")
    number_of_days_temp = fields.Float(
        'Allocation', copy=False, readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help='Number of days of the leave request according to your working schedule.')
    hr_job = fields.Many2one('hr.job','Designation')
    emp_id = fields.Char(related='employee_id.emp_id', string='Employee ID')
    holiday_type = fields.Selection([
        ('employee', 'Employee'),
        ('category', 'Employee All')
    ], string='Allocation Mode', readonly=True, required=True, default='employee',
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help='By Employee: Allocation/Request for individual Employee, Employee All: Allocation/Request for group of employees')
    employee_id = fields.Many2one('hr.employee', string='Employee', index=True, readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, default=False, track_visibility='onchange')

    date_from = fields.Date('Start Date', readonly=True, index=True, copy=False,
            states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    date_to = fields.Date('End Date', readonly=True, copy=False,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    
    year_of_passing = fields.Selection([(num, str(num)) for num in range(((datetime.now().year)), ((datetime.now().year)+2))], 'Year',default=datetime.now().year)
    available_balance_leave_till = fields.Float(string='Leaves available', compute='calc_leave_till')
    accrued_leaves = fields.Float(string='Accrued Leaves', compute='calc_leave_till')

    
    holiday_calendar_line = fields.One2many('hr.holidays.calendar.line','holidays_id','Leave Details')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('confirm', 'Requested'),
        ('cancel', 'Cancelled'),
        ('refuse', 'Rejected'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft',
        help="The status is set to 'To Submit', when a leave request is created." +
             "\nThe status is 'To Approve', when leave request is confirmed by user." +
             "\nThe status is 'Rejected', when leave request is refused by manager." +
             "\nThe status is 'Approved', when leave request is approved by manager.")

    number_of_days = fields.Float('Number of Days Applied', compute='_compute_number_of_days', store=True,track_visibility='onchange',)
    leave_request_remarks_line = fields.One2many('leave.request.remarks.line', 'leave_request_id', string='Leave Request Remarks Line', ondelete='cascade')

    
    def sub_main_monthly_one_time_leave_allocation_update(self):
        self.env.cr.execute("""select monthly_one_time_leave_allocation_update();""")
        return True
        
    @api.multi
    def sub_main_monthly_one_time_leave_allocation_function_creation_one(self):
        self.env.cr.execute("""DROP FUNCTION IF EXISTS months_between (t_start timestamp, t_end timestamp);""")
        self.env.cr.execute("""
                                CREATE FUNCTION months_between (t_start timestamp, t_end timestamp)
                                RETURNS integer
                                AS $$
                                    SELECT
                                        (
                                            12 * extract('years' from a.i) + extract('months' from a.i)
                                        )::integer
                                    from (
                                        values (justify_interval($2 - $1))
                                    ) as a (i)
                                $$
                                LANGUAGE SQL
                                IMMUTABLE
                                RETURNS NULL ON NULL INPUT;
                            """)
            
    
    @api.multi
    def sub_main_monthly_one_time_leave_allocation_function_creation_two(self):
        self.env.cr.execute("""  
                                CREATE OR REPLACE FUNCTION monthly_one_time_leave_allocation_update() RETURNS INTEGER AS $$
                                DECLARE
                                    employee RECORD;
                                    holiday_status RECORD;
                                    employee_allocation_count FLOAT;
                                    --employee_remove_count FLOAT;
                                    employee_new_allocation_count FLOAT;
                                    current_year INTEGER ;
                                    seq_hr_holidays_Id INTEGER;
                                    Office_id INTEGER;
                                    ESI_applicable BOOLEAN;
                                    Date_of_joining_next_month_start_date VARCHAR;
                                    month_count INTEGER;
                                    today_date VARCHAR;
                                    Gender_name VARCHAR;
                                    new_leave_count FLOAT;
                                    --raise notice 'Inserting CURRENT DATE %',select extract(year from now()::date)::integer; 
                                          
                                    employee_list_cur CURSOR FOR select * from hr_employee where active = True ORDER BY branch_id,id;
                                    holiday_status_list_cur CURSOR FOR select * from hr_holidays_status where active = True and leave_auto_allocation=True ORDER BY id;
                                    
                                BEGIN
                                    OPEN employee_list_cur;
                                    LOOP
                                        FETCH employee_list_cur INTO employee;
                                        EXIT WHEN NOT FOUND;
                                        select extract(year from now()::date)::integer INTO   current_year; 
                                        employee_allocation_count =0.00;
                                        --employee_remove_count =0.00;
                                        employee_new_allocation_count = 0.00;
                                        Date_of_joining_next_month_start_date = '';
                                        month_count = 0;
                                        select employee.unit_type_id INTO Office_id;
                                        select is_esi_applicable INTO ESI_applicable from operating_unit where id=employee.branch_id;
                                        
                                        select name INTO Gender_name from pappaya_gender where id=employee.gender_id;
                                                     
                                        select now()::date::VARCHAR INTO today_date;                                    
    
                                        OPEN holiday_status_list_cur;
                                                    
                                        LOOP
                                            FETCH holiday_status_list_cur INTO holiday_status;
                                            EXIT WHEN NOT FOUND;
                                                IF (holiday_status.code = 'SL') THEN
    --raise notice 'DFGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG %',employee.gross_salary ;
                                                    IF  ( employee.gross_salary > 21000 and ESI_applicable IS TRUE) THEN
                                                        raise notice 'Inserting employee DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD%',employee.id; 
                                                        select COALESCE(sum( number_of_days_temp ),0) INTO employee_allocation_count from hr_holidays where employee_id = employee.id and type = 'add' and state = 'validate' and to_carry_forward_leave IS NULL
                                                        and holiday_status_id =holiday_status.id and year_of_passing = current_year;
                                                        
                                                        --select COALESCE(sum( number_of_days_temp ),0) INTO employee_remove_count from hr_holidays where 
                                                        --employee_id = employee.id and type = 'remove' and state = 'validate'
                                                        --and holiday_status_id =holiday_status.id and year_of_passing = current_year;
                                                        --select no_of_leave_allocation(employee.id , employee.date_of_joining,holiday_status.id,holiday_status.max_allowed_days,employee_allocation_count) INTO                                 --employee_new_allocation_count;
                                                       
                                                       raise notice 'Inserting employee_new_allocation_count end %',employee_new_allocation_count;                    
                                                        
                                                        --SELECT (::date + INTERVAL '1 months')::date INTO 
                                                        raise notice 'Inserting employee.date_of_joining::date %',employee.date_of_joining::date;
                                                        select concat(EXTRACT(YEAR from (employee.date_of_joining::date + INTERVAL '1 months')::date)::VARCHAR,'-'::VARCHAR,EXTRACT(MONTH from  (employee.date_of_joining::date ::date + INTERVAL '1 months')::date)::VARCHAR,'-'::VARCHAR,'01'::VARCHAR)::date
                                                        INTO Date_of_joining_next_month_start_date;
                                                        
                                                        --raise notice 'Inserting Date_of_joining_next_month_start_date %',Date_of_joining_next_month_start_date;
                                                        IF (EXTRACT(YEAR from Date_of_joining_next_month_start_date::date) = EXTRACT(YEAR from now()::date)) THEN
                                                            select abs(months_between(now()::date,Date_of_joining_next_month_start_date::date)) INTO month_count;
                                                            --raise notice 'month_count %',month_count;
                                                            IF (month_count > 0) THEN
                                                                new_leave_count = 0;
                                                                new_leave_count =    month_count * holiday_status.max_allowed_days/12;
                                                                IF employee_allocation_count < holiday_status.max_allowed_days THEN
                                                                    employee_new_allocation_count = abs(employee_allocation_count - new_leave_count);
                                                                   -- raise notice 'Inserting employee_new_allocation_count end 222222222 %',employee_new_allocation_count;
                                                                END IF;
                                                            END IF;
                                                        ELSE
                                                            IF employee_allocation_count < holiday_status.max_allowed_days THEN
                                                                employee_new_allocation_count = abs(holiday_status.max_allowed_days - employee_allocation_count);
                                                               -- raise notice 'Inserting employee_new_allocation_count end 333333333333 %',employee_new_allocation_count;
                                                            END IF;
                                                            
                                                        END IF;
                                                        
                                                        
                                                        IF (employee_new_allocation_count > 0 and Office_id = holiday_status.office_type_id) THEN 
                                                            raise notice 'Inserting employee_new_allocation_count end 4444444444444 %',employee_new_allocation_count;           
                                                            select COALESCE (max(id + 1 ),1) INTO seq_hr_holidays_Id from hr_holidays ;
                                                            INSERT INTO hr_holidays(id,employee_id,name,state,holiday_status_id,number_of_days_temp,number_of_days,type,holiday_type,year_of_passing,office_type_id,department_id,create_uid,create_date,write_uid,write_date) 
                                                            VALUES (seq_hr_holidays_Id,employee.id,holiday_status.name,'validate',holiday_status.id,employee_new_allocation_count,employee_new_allocation_count,'add','employee',current_year,Office_id,employee.department_id,1,now(),1,now());
                                                        END IF;
                                                    END IF;                        
                                                ELSE
                                                    raise notice 'Inserting employee %',employee.id; 
                                                    
                                                    
                                                    select COALESCE(sum( number_of_days_temp ),0) INTO employee_allocation_count from hr_holidays where employee_id = employee.id and type = 'add' and state = 'validate' and to_carry_forward_leave IS NULL
                                                    and holiday_status_id =holiday_status.id and year_of_passing = current_year;
                                                    
                                                    --select COALESCE(sum( number_of_days_temp ),0) INTO employee_remove_count from hr_holidays where 
                                                    --employee_id = employee.id and type = 'remove' and state = 'validate'
                                                    --and holiday_status_id =holiday_status.id and year_of_passing = current_year;
                                                    --select no_of_leave_allocation(employee.id , employee.date_of_joining,holiday_status.id,holiday_status.max_allowed_days,employee_allocation_count) INTO                                 --employee_new_allocation_count;
                                                   
                                                   raise notice 'Inserting employee_new_allocation_count end %',employee_new_allocation_count;                    
                                                    
                                                    --SELECT (::date + INTERVAL '1 months')::date INTO 
                                                    raise notice 'Inserting employee.date_of_joining::date %',employee.date_of_joining::date;
                                                    select concat(EXTRACT(YEAR from (employee.date_of_joining::date + INTERVAL '1 months')::date)::VARCHAR,'-'::VARCHAR,EXTRACT(MONTH from  (employee.date_of_joining::date ::date + INTERVAL '1 months')::date)::VARCHAR,'-'::VARCHAR,'01'::VARCHAR)::date
                                                    INTO Date_of_joining_next_month_start_date;
                                                    
                                                    raise notice 'Inserting Date_of_joining_next_month_start_date %',Date_of_joining_next_month_start_date;
                                                    IF (EXTRACT(YEAR from Date_of_joining_next_month_start_date::date) = EXTRACT(YEAR from now()::date)) THEN
                                                        select abs(months_between(now()::date,Date_of_joining_next_month_start_date::date)) INTO month_count;
                                                        raise notice 'month_count %',month_count;
                                                        IF (month_count > 0) THEN
                                                            new_leave_count = 0;
                                                            new_leave_count =    month_count * holiday_status.max_allowed_days/12;
                                                            IF employee_allocation_count < holiday_status.max_allowed_days THEN
                                                                employee_new_allocation_count = abs(employee_allocation_count - new_leave_count);
                                                                raise notice 'Inserting employee_new_allocation_count end 222222222 %',employee_new_allocation_count;
                                                            END IF;
                                                        END IF;
                                                    ELSE
                                                        IF employee_allocation_count < holiday_status.max_allowed_days THEN
                                                            employee_new_allocation_count = abs(holiday_status.max_allowed_days - employee_allocation_count);
                                                            raise notice 'Inserting employee_new_allocation_count end 333333333333 %',employee_new_allocation_count;
                                                        END IF;
                                                        
                                                    END IF;
                                                    IF (holiday_status.code = 'PTL' and Gender_name = 'Male' and holiday_status.gender = 'male') THEN
                                                        IF (employee_new_allocation_count > 0 and Office_id = holiday_status.office_type_id) THEN 
                                                            raise notice 'Inserting employee_new_allocation_count end 4444444444444 %',employee_new_allocation_count;           
                                                            select COALESCE (max(id + 1 ),1) INTO seq_hr_holidays_Id from hr_holidays ;
                                                            INSERT INTO hr_holidays(id,employee_id,name,state,holiday_status_id,number_of_days_temp,number_of_days,type,holiday_type,year_of_passing,office_type_id,department_id,create_uid,create_date,write_uid,write_date) 
                                                            VALUES (seq_hr_holidays_Id,employee.id,holiday_status.name,'validate',holiday_status.id,employee_new_allocation_count,employee_new_allocation_count,'add','employee',current_year,Office_id,employee.department_id,1,now(),1,now());
                                                        END IF;
                                                    ELSIF (holiday_status.code != 'PTL') THEN
                                                        IF (employee_new_allocation_count > 0 and Office_id = holiday_status.office_type_id) THEN 
                                                            raise notice 'Inserting employee_new_allocation_count end 4444444444444 %',employee_new_allocation_count;           
                                                            select COALESCE (max(id + 1 ),1) INTO seq_hr_holidays_Id from hr_holidays ;
                                                            INSERT INTO hr_holidays(id,employee_id,name,state,holiday_status_id,number_of_days_temp,number_of_days,type,holiday_type,year_of_passing,office_type_id,department_id,create_uid,create_date,write_uid,write_date) 
                                                            VALUES (seq_hr_holidays_Id,employee.id,holiday_status.name,'validate',holiday_status.id,employee_new_allocation_count,employee_new_allocation_count,'add','employee',current_year,Office_id,employee.department_id,1,now(),1,now());
                                                        END IF;
                                                    END IF;
                                                END IF;
                            
                                        END LOOP;
                                        CLOSE holiday_status_list_cur;
                            
                                    END LOOP;
                                    CLOSE employee_list_cur;
                                    IF seq_hr_holidays_Id > 0 THEN
                                      PERFORM setval('hr_holidays_id_seq', COALESCE((SELECT MAX(id)+1 FROM hr_holidays), 1), false);
                                    END IF;
                                 RETURN 0;  
                            END;  $$
                        LANGUAGE plpgsql; 
                        """)
    
            
    @api.multi       
    def main_schedule_monthly_one_time_leave_allocation_update(self):
        self.Event = threading.Event
        t = threading.Thread(name="%s.Bus" % __name__, target=self.sub_main_monthly_one_time_leave_allocation_update, args=())
        t.daemon = True
        t.start()
        return True
    
    
    
    @api.multi
    def yearly_update_and_insert_carryforward_leaves_two(self):
        self.Event = threading.Event
        t = threading.Thread(name="%s.Bus" % __name__, target=self.yearly_update_and_insert_carryforward_leaves, args=())
        t.daemon = True
        t.start()
        return True
    
    def yearly_update_and_insert_carryforward_leaves(self):
        self.env.cr.execute("""select yearly_update_and_insert_carryforward_leaves();""")
    
    def yearly_update_and_insert_carryforward_leaves_one(self):
        self.env.cr.execute(""" CREATE OR REPLACE FUNCTION yearly_update_and_insert_carryforward_leaves() RETURNS INTEGER AS $$
                            DECLARE
                                employee RECORD;
                                holiday_status RECORD;

                                Office_id INTEGER;
                                current_year INTEGER ;
                                Previous_year INTEGER ;
                                employee_leave_carryforward_count INTEGER;
                                fund_leave_encashment INTEGER;


                                employee_allocation_count FLOAT;
                                employee_remove_count FLOAT;
                                employee_new_allocation_count FLOAT;

                                seq_hr_holidays_Id INTEGER;
                                seq_leave_encashment_request_id INTEGER;



                                employee_list_cur CURSOR FOR select * from hr_employee where active = True ORDER BY branch_id,id;
                                holiday_status_list_cur CURSOR FOR select * from hr_holidays_status where active = True and carry_forward='yes' ORDER BY id;

                            BEGIN
                                OPEN employee_list_cur;
                                LOOP
                                    FETCH employee_list_cur INTO employee;
                                    EXIT WHEN NOT FOUND;




                                    employee_allocation_count =0.00;
                                    employee_remove_count =0.00;
                                    employee_new_allocation_count = 0.00;
                                    fund_leave_encashment = 0;
                                    employee_leave_carryforward_count = 0;

                                    select office_type_id INTO Office_id from operating_unit where id=employee.branch_id;

                                    OPEN holiday_status_list_cur;

                                    LOOP
                                        FETCH holiday_status_list_cur INTO holiday_status;
                                        EXIT WHEN NOT FOUND;
                                            raise notice 'Inserting employee %',employee.id;
                                            select extract(year from now()::date)::integer INTO   current_year;
                                            previous_year = current_year - 1;

                                            SELECT COALESCE(sum( abs(number_of_days_temp) ),0.00) INTO employee_allocation_count from hr_holidays
                                            where employee_id = employee.id and type = 'add' and state = 'validate' and holiday_status_id =holiday_status.id
                                            and year_of_passing = Previous_year;

                                            SELECT COALESCE(sum( abs(number_of_days_temp) ),0.00) INTO employee_remove_count from hr_holidays where
                                            employee_id = employee.id and type = 'remove' and state = 'validate'
                                            and holiday_status_id =holiday_status.id and year_of_passing = Previous_year;

                                            SELECT count(*) INTO fund_leave_encashment from leave_encashment_request where employee_id = employee.id
                                            and year = current_year and state != 'rejected';

                                            employee_new_allocation_count = abs(employee_allocation_count) - abs(employee_remove_count);

                                            select id INTO  seq_leave_encashment_request_Id from leave_encashment_request where employee_id = employee.id and
                                            state='carry_forward' and year=Previous_year and carryforward_year=current_year and type='carry_forward' limit 1;

                                            raise notice 'Inserting employee_new_allocation_count end %',fund_leave_encashment;
                                            IF (employee_new_allocation_count > 0) THEN
                                                IF (seq_leave_encashment_request_Id > 0) THEN
                                                    IF (fund_leave_encashment = 0 and Office_id = holiday_status.office_type_id) THEN
    
                                                        select leave_balance_count INTO  employee_leave_carryforward_count from leave_encashment_request where id = seq_leave_encashment_request_Id;
    
                                                        UPDATE leave_encashment_request SET leave_balance_count = leave_balance_count + employee_new_allocation_count where id = seq_leave_encashment_request_Id;
    
                                                        SELECT COALESCE((SELECT MAX(id)+1 FROM hr_holidays), 1) INTO seq_hr_holidays_Id;
    
                                                        INSERT INTO hr_holidays(id,employee_id,name,state,holiday_status_id,number_of_days_temp,number_of_days,type,holiday_type,year_of_passing,office_type_id,department_id,from_carry_forward_leave,create_uid,create_date,write_uid,write_date)
                                                        VALUES (seq_hr_holidays_Id,employee.id,holiday_status.name,'validate',holiday_status.id,abs(employee_new_allocation_count),abs(employee_new_allocation_count),'add','employee',current_year,Office_id,employee.department_id,seq_leave_encashment_request_Id,1,now(),1,now());
                                                    END IF;
    
                                                ELSE
                                                    IF (fund_leave_encashment = 0 and Office_id = holiday_status.office_type_id) THEN
    
                                                        SELECT COALESCE((SELECT MAX(id)+1 FROM leave_encashment_request), 1) INTO seq_leave_encashment_request_Id;
    
                                                        INSERT INTO leave_encashment_request(id,employee_id,requested_date,state,year,carryforward_year,leave_balance_count,type)
                                                        VALUES(seq_leave_encashment_request_Id,employee.id,now()::date,'carry_forward',Previous_year,current_year,employee_new_allocation_count,'carry_forward');
    
                                                        SELECT COALESCE((SELECT MAX(id)+1 FROM hr_holidays), 1) INTO seq_hr_holidays_Id;
    
                                                        INSERT INTO hr_holidays(id,employee_id,name,state,holiday_status_id,number_of_days_temp,number_of_days,type,holiday_type,year_of_passing,office_type_id,department_id,from_carry_forward_leave,create_uid,create_date,write_uid,write_date)
                                                        VALUES (seq_hr_holidays_Id,employee.id,holiday_status.name,'validate',holiday_status.id,abs(employee_new_allocation_count),abs(employee_new_allocation_count),'add','employee',current_year,Office_id,employee.department_id,seq_leave_encashment_request_Id,1,now(),1,now());
                                                    END IF;
                                                END IF;
                                            END IF;
                                            raise notice 'Inserting employee_new_allocation_count end %',employee_new_allocation_count;

                                    END LOOP;
                                    CLOSE holiday_status_list_cur;

                                END LOOP;
                                CLOSE employee_list_cur;
                             PERFORM setval('leave_encashment_request_id_seq', COALESCE((SELECT MAX(id)+1 FROM leave_encashment_request), 1), false);
                             PERFORM setval('hr_holidays_id_seq', COALESCE((SELECT MAX(id)+1 FROM hr_holidays), 1), false);

                             RETURN 0;
                        END; $$ LANGUAGE PLPGSQL""")
    
    
    
    
    def action_cancel(self):
        for record in self:
            record.state = 'cancel'

    @api.onchange('holiday_calendar_line')
    def onchange_work_type_holiday_calendar_line(self):
        for record in self:
            days = 0.00
            for line in record.holiday_calendar_line:
                if line.parts_of_the_day == 'half_day':
                    days += 0.5
                else:
                    days += 1
            print (days,"123333333333344444444444444444444444444444444444444")
            record.number_of_days_temp = days

    @api.model
    def create(self, vals):
        if vals.get('type') == 'remove':
            emp_obj = self.env['hr.employee'].browse(vals.get('employee_id'))
            emp_obj.date_of_joining
            
            start_date = date(date.today().year, 1, 1)
            end_date = date(date.today().year, 12, 31)
            print('start_date : ', start_date)
            print('end_date : ', end_date)
            
            doj = datetime.strptime(emp_obj.date_of_joining, "%Y-%m-%d").date()
            print('doj : ', doj)
            if doj >= start_date and doj <= end_date:
                print('emp_obj.date_of_joining.month  : ',emp_obj.date_of_joining[5:7])
                leave_typ_obj = self.env['hr.holidays.status'].browse(vals.get('holiday_status_id'))
                leave_typ_obj.max_allowed_days
                leave_typ_obj.per_month_days
                permonth_allowed_count = leave_typ_obj.max_allowed_days / 12
                starting_date_month = emp_obj.date_of_joining[5:7]
                ending_date_month = str(end_date)[5:7]
                
                date1 = datetime.strptime(str(end_date), '%Y-%m-%d')
                date2 = datetime.strptime(str(emp_obj.date_of_joining), '%Y-%m-%d')
                r = relativedelta(date1, date2)
                r.months
                
                
                allcated_per_year = round(r.months * permonth_allowed_count)
                
                taken_leave = 0
                for rec in self.search([('type','=','remove'),('employee_id','=',vals.get('employee_id')),
                             ('holiday_status_id','=',vals.get('holiday_status_id')),('year_of_passing','=',vals.get('year_of_passing'))]):
                    taken_leave += rec.number_of_days_temp
                
                
                number_of_days_temp = vals.get('number_of_days_temp')
                
                allcated_per_year = allcated_per_year - taken_leave
                
                holiday_status_id = self.env['hr.holidays.status'].search([('code','in',['LWP','OD','SPL'])])
                
                if number_of_days_temp > allcated_per_year and  vals.get('holiday_status_id') not in holiday_status_id.ids:
                    raise ValidationError(_('Your remaining leaves for this year is "%s"') % (allcated_per_year))
                
                if number_of_days_temp > leave_typ_obj.per_month_days and  vals.get('holiday_status_id') not in holiday_status_id.ids:
                    raise ValidationError(_('Your are allowed to take "%s" day leave per month.') % (leave_typ_obj.per_month_days))
                
                print('permonth_allowed_count : ', permonth_allowed_count)
                print('starting_date_month : ', starting_date_month)
                print('ending_date_month : ', ending_date_month)
                
                print('r.months : ', r.months)
                print('fv : ', allcated_per_year)
                print('leave_typ_obj.per_month_days  : ', leave_typ_obj.per_month_days)
                
                print('*****************************************************************')
#                 self.env[''].search([('','',''),('','','')])
                    
#                 vals['operating_unit_id'] = move.operating_unit_id.id
#         raise ValidationError(_('Date To should be greater than Date From'))
        return super(HrHolidays, self).create(vals)

    @api.constrains('date_from', 'date_to')
    def check_from_to_date(self):
        for record in self:
            if record.date_from and record.date_to:
#                 if datetime.strptime(record.date_from, DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date() \
#                         or datetime.strptime(record.date_from, DEFAULT_SERVER_DATE_FORMAT).date() < datetime.now().date():
#                     raise ValidationError('Please check the dates, Past dates are not allowed')
                if record.date_from > record.date_to:
                    raise ValidationError(_('Date To should be greater than Date From'))
                
                if (record.date_from or record.date_to) < record.employee_id.date_of_joining:
                    doj = parser.parse(record.employee_id.date_of_joining)
                    proper_doj = doj.strftime('%d-%m-%Y')
                    raise ValidationError(_("Dates are not Acceptable.\n It must be greater than Employee's Date of Joining %s ") % (proper_doj))
    
    from_carry_forward_leave = fields.Many2one('leave.encashment.request',string='From Carry-Forward Leave')  
    to_carry_forward_leave = fields.Many2one('leave.encashment.request',string='To Carry-Forward Leave')
    encashment_leave = fields.Many2one('leave.encashment.request',string='To Carry-Forward Leave')
    

    @api.constrains('date_from', 'date_to','holiday_status_id','year_of_passing','employee_id')
    def _check_date(self):
        for holiday in self:
            holiday_status_id = holiday.holiday_status_id
            if holiday.type  == 'remove':
                
                # Previous date and next date leave if there raise waring message                     
                start = datetime.strptime(holiday.date_from, '%Y-%m-%d').date() + timedelta(days=-1)
                end = datetime.strptime(holiday.date_to, '%Y-%m-%d').date() + timedelta(days=+1)
                domain = [
                    ('employee_id', '=', holiday.employee_id.id),
                    ('id', '!=', holiday.id),
                    ('type', '=', 'remove'),
                    ('year_of_passing','=',holiday.year_of_passing),
                    ('state', 'not in', ['cancel', 'refuse'])]
                previous_holidays_sr            = self.search(domain)
                pre_holiday_calendar_line_sr    = holiday.holiday_calendar_line.search_count([('date','=',start),
                                                                                 ('holidays_id','in',previous_holidays_sr.ids)])
                next_holiday_calendar_line_sr   = holiday.holiday_calendar_line.search_count([('date','=',end),
                                                                                 ('holidays_id','in',previous_holidays_sr.ids)])
                if pre_holiday_calendar_line_sr and holiday.holiday_status_id.code not in ['LWP','OD','SPL']:
                    raise ValidationError(_("You are not allowed to avail different leave types consecutively"))
                if next_holiday_calendar_line_sr and holiday.holiday_status_id.code not in ['LWP','OD','SPL']:
                    raise ValidationError(_("You are not allowed to avail different leave types consecutively"))
                if holiday.number_of_days_temp > holiday.accrued_leaves and holiday.holiday_status_id.code not in ['LWP','OD','SPL']:
                    raise ValidationError(_('You are exceeding the Accrued Leave still current month %s') % str(holiday.accrued_leaves))
                if holiday_status_id.code =='MTL':
                    if holiday.employee_id.gender_id.name == 'Female':
                        if holiday.employee_id.marital in ['single']:
                            raise ValidationError(_('This leave type not allowed for marital status: Single or Widower'))
                        domain = [
                        ('employee_id', '=', holiday.employee_id.id),
                        ('id', '!=', holiday.id),
                        ('type', '=', 'remove'),
                        ('year_of_passing','=',holiday.year_of_passing),
                        ('holiday_status_id','=',holiday_status_id.id),
                        ('state', 'not in', ['cancel', 'refuse'])]
                        mtl_holidays_sr = self.search_count(domain)
                        if mtl_holidays_sr > 1:
                            raise ValidationError(_('This leave type(%s) is  allowed only Two times in your service. \n You have already availed Two times of leave in your service')% str(holiday_status_id.name))
                    else:
                        raise ValidationError(_('This leave type is allowed for Female employees'))

                if holiday_status_id.code == 'PTL':
                    if holiday.employee_id.gender_id.name == 'Male':
                        domain = [
                        ('employee_id', '=', holiday.employee_id.id),
                        ('id', '!=', holiday.id),
                        ('type', '=', 'remove'),
                        ('year_of_passing','=',holiday.year_of_passing),
                        ('holiday_status_id','=',holiday_status_id.id),
                        ('state', 'not in', ['cancel', 'refuse'])]
                        mtl_holidays_sr = self.search_count(domain)
                        if mtl_holidays_sr > 1:
                            raise ValidationError(_('This leave type(%s) is allowed Two times of your service')% str(holiday_status_id.name))

                    else:
                        raise ValidationError(_('This leave type is  allowed for Male employees'))
                    
                if holiday_status_id.code == 'PL':
                        domain = [
                        ('employee_id', '=', holiday.employee_id.id),
                        ('id', '!=', holiday.id),
                        ('type', '=', 'remove'),
                        ('year_of_passing','=',holiday.year_of_passing),
                        ('holiday_status_id','=',holiday_status_id.id),
                        ('state', 'not in', ['cancel', 'refuse'])]
                        mtl_holidays_sr = self.search_count(domain)
                        if mtl_holidays_sr > 3:
                            raise ValidationError(_('This leave type(%s) is allowed Three times of your service')% str(holiday_status_id.name))
                
                
                if holiday_status_id.code not in ['LWP','OD','SPL']:
                    
                    domain = [
                        ('employee_id', '=', holiday.employee_id.id),
                        ('type', '=', 'add'),
                        ('to_carry_forward_leave', '=', False),
                        ('year_of_passing','=',holiday.year_of_passing),
                        ('holiday_status_id','=',holiday_status_id.id),
                        ('state', 'not in', ['cancel', 'refuse'])]
                    mtl_holidays_sr = self.search_count(domain)
                    if not mtl_holidays_sr:
                        raise ValidationError(_('Please allocate leave for %s')% str(holiday_status_id.name))
                
                for line in holiday.holiday_calendar_line:
                    domain = [
                        ('employee_id', '=', holiday.employee_id.id),
                        ('id', '!=', holiday.id),
                        ('type', '=', 'remove'),
                        ('year_of_passing','=',holiday.year_of_passing),
                        ('state', 'not in', ['cancel', 'refuse'])]
                    holidays_sr = self.search(domain)
                    holiday_calendar_line_sr = holiday.holiday_calendar_line.search_count([('date','=',line.date),
                                                                                     ('holidays_id','in',holidays_sr.ids)])
                    if holiday_calendar_line_sr:
                        raise ValidationError(_('Already Leave Request apply on  %s') % str(line.date))

                number_of_days_temp             = holiday.number_of_days_temp
                available_balance_leave_till    = holiday.available_balance_leave_till
                per_month_days                  = holiday.holiday_status_id.per_month_days
                already_taken_number_of_days_temp = 0.00
                if number_of_days_temp > available_balance_leave_till and holiday.holiday_status_id.code not in ['LWP','OD','SPL']:
                    raise ValidationError(_('You are exceeding the leave balance available till current month %s') % str(holiday.available_balance_leave_till))

                if holiday.holiday_calendar_line:
                    calendar_line_first_date    =   holiday.holiday_calendar_line[0].date 
                    calendar_line_last_date     =   holiday.holiday_calendar_line[-1].date
                    calendar_line_first_date = datetime.strptime(calendar_line_first_date, "%Y-%m-%d").date()
                    calendar_line_last_date = datetime.strptime(calendar_line_last_date, "%Y-%m-%d").date()
                    calendar_line_first_date = calendar_line_first_date.replace(day=1)
                    
                    month_last_date = calendar.monthrange(calendar_line_last_date.year, calendar_line_last_date.month)[1]
                    leave_request_month_last_date = calendar_line_last_date.replace(day=month_last_date)
                    total_months = 0.00
                    rd = relativedelta(leave_request_month_last_date,calendar_line_first_date)
                    months =  rd.months
                    days = rd.days
                    if days:
                        total_months = months + 1
                    else:
                        total_months = months
    
                    this_month_available_days = 0.00
                    if calendar_line_first_date and leave_request_month_last_date:
                        domain = [
                            ('employee_id', '=', holiday.employee_id.id),
                            ('id', '!=', holiday.id),
                            ('type', '=', 'remove'),
                            ('year_of_passing','=',holiday.year_of_passing),
                            ('holiday_status_id','=',holiday_status_id.id),
                            ('state', 'not in', ['cancel', 'refuse'])]
                        holidays_sr = self.search(domain)
                        holiday_calendar_line_sr = holiday.holiday_calendar_line.search_count([('date','>=',calendar_line_first_date),
                                                                                         ('date','<=',leave_request_month_last_date),
                                                                                         ('holidays_id','in',holidays_sr.ids)])
    
    
                        remaining_days = total_months * per_month_days - holiday_calendar_line_sr
                        if number_of_days_temp > remaining_days and remaining_days > 0 and holiday.holiday_status_id.code not in ['LWP','OD','SPL']:
                            raise ValidationError(_('You are not allowed to apply leave allotted for this month %s') % str(remaining_days))
                        elif number_of_days_temp and remaining_days <= 0 and holiday.holiday_status_id.code not in ['LWP','OD','SPL']:
                            a = str(total_months * per_month_days)
                            b = str(holiday_calendar_line_sr)
                            raise ValidationError(_('You are not allowed to apply leave allotted for this month %s and already taken %s')%(a,b))
                        
                    leave_weekly_holiday_only = holiday.holiday_calendar_line.search([('id','in',holiday.holiday_calendar_line.ids),('work_type','=','work')])
                    if not leave_weekly_holiday_only:
                        raise ValidationError(_('You are not allowed to apply leave on Weeklyoff/Holiday'))
                else:
                    raise ValidationError(_(' Please create calendar for the selected leave duration'))
                   
                
            
            
            
    
    @api.depends('holiday_status_id','date_from','date_to','year_of_passing','employee_id')
    def calc_leave_till(self):
        for record in self:
            
            if record.type == 'remove' and record.year_of_passing and record.holiday_status_id.code not in ['LWP','OD','SPL'] and record.employee_id:
                already_allocate_leave = 0.00
                already_taken_leave = 0.00
                per_month_days      = record.holiday_status_id.per_month_days
                for leaves in self.env['hr.holidays'].search([('employee_id', '=', record.employee_id.id),
                                                      ('type','=','add'),
                                                      ('state','=','validate'),
                                                      ('to_carry_forward_leave','=',False),
                                                      ('holiday_status_id', '=', record.holiday_status_id.id),
                                                      ('year_of_passing','=',record.year_of_passing)]):
                    already_allocate_leave += leaves.number_of_days_temp
                for leave_taken in self.env['hr.holidays'].search([
                                                                        ('employee_id', '=', record.employee_id.id),
                                                                        ('type','=','remove'),
                                                                        ('state','=','validate'),
                                                                        ('holiday_status_id', '=', record.holiday_status_id.id),
                                                                        ('year_of_passing','=',record.year_of_passing)
                                                                    ]):
                    already_taken_leave += leave_taken.number_of_days_temp
                    
                remaining_leave = 0.00
                if  already_allocate_leave >=   already_taken_leave: 
                    remaining_leave = already_allocate_leave  - already_taken_leave
                if 0.00 < remaining_leave and already_allocate_leave:
                    record.available_balance_leave_till = remaining_leave
                else:
                    record.available_balance_leave_till = remaining_leave
                
                # 
                today                           = datetime.now().date()
                date_of_joining                 = datetime.strptime(record.employee_id.date_of_joining, "%Y-%m-%d").date()
                next_month_from_date_of_joining = date_of_joining + relativedelta(months=+1, day=1)
                
                year_start_date                 = date(int(today.year), 1, 1)
                current_month_end_date          = today + relativedelta(months=+1, day=1, days=-1)
                
                already_allocate_leave = 0.00
                remove_leave = 0.00
                for leaves in self.env['hr.holidays'].search([('employee_id', '=', record.employee_id.id),
                                                      ('type','=','add'),
                                                      ('state','=','validate'),
                                                      ('holiday_status_id', '=', record.holiday_status_id.id),
                                                      ('year_of_passing','=',record.year_of_passing)]):
                    already_allocate_leave += leaves.number_of_days_temp
                for remove_leaves in self.env['hr.holidays'].search([('employee_id', '=', record.employee_id.id),
                                                          ('type','=','remove'),
                                                          ('state','=','validate'),
                                                          ('year_of_passing','=',record.year_of_passing),
                                                          ('holiday_status_id', '=', record.holiday_status_id.id)]):
                    remove_leave += remove_leaves.number_of_days_temp
                
                total_months = 0
                one_month_allowed_leave = record.holiday_status_id.accrued_leaves
                if next_month_from_date_of_joining.year == current_month_end_date.year:
                    print ("11111111111111111111")
                    rd = relativedelta(next_month_from_date_of_joining,current_month_end_date)
                    months =  abs(rd.months)
                    days = abs(rd.days)
                    if days:
                        total_months = months + 1
                    else:
                        total_months = months
                else:
                    print ("222222222222222222")
                    rd = relativedelta(year_start_date,current_month_end_date)
                    months =  abs(rd.months)
                    days = abs(rd.days)
                    print (rd,months,days,"DSSSSSSSSSSSSSSSSSSSSSSSSS")
                    if days:
                        total_months = months + 1
                    else:
                        total_months = months
                
                total_leaves = (one_month_allowed_leave * total_months)
                if already_allocate_leave < total_leaves:
                    total_leaves = already_allocate_leave
                print (one_month_allowed_leave,total_months,remove_leave,"SSSSSSSSSSSSSSSSSSSSSSSSSSSS")
                if remove_leave > 0:
                    record.accrued_leaves   = total_leaves - remove_leave
                else:
                    record.accrued_leaves   = total_leaves
                        
    
    @api.multi
    def generate_dates(self, date_from, date_to):
        dates = []
        td = timedelta(days=1)
        current_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        while current_date <= datetime.strptime(date_to, "%Y-%m-%d").date():
            dates.append(current_date)
            current_date += td
        return dates
    
    @api.onchange('office_type_id')
    def _onchange_office_type_id(self):
        if self.office_type_id:
            self.holiday_status_id = None
    
    @api.onchange('date_from')
    def _onchange_date_from(self):
        for record in self:
            record._onchange_date_to()

    @api.one
    def copy(self, default=None):
        raise ValidationError('Sorry, You are not allowed to Duplicate')

    @api.constrains('state', 'number_of_days_temp', 'holiday_status_id')
    def _check_holidays(self):
        for holiday in self:
            if holiday.holiday_type != 'employee' or holiday.type != 'remove' or not holiday.employee_id or holiday.holiday_status_id.limit :
                continue
            if holiday.holiday_status_id.code in ['LWP','OD','SPL']:
                 continue
            leave_days = holiday.holiday_status_id.get_days(holiday.employee_id.id)[holiday.holiday_status_id.id]
            if float_compare(leave_days['remaining_leaves'], 0, precision_digits=2) == -1 or \
              float_compare(leave_days['virtual_remaining_leaves'], 0, precision_digits=2) == -1:
                raise ValidationError(_('The number of remaining leaves is not sufficient for this leave type.\n'
                                        'Please verify also the leaves waiting for validation.'))
    
    @api.constrains('holiday_status_id', 'employee_id', 'number_of_days_temp', 'year_of_passing')
    def check_work_days(self):
        for record in self:
            if record.employee_id and record.holiday_status_id and record.holiday_status_id.work_days:
                if record.employee_id.working_days <= record.holiday_status_id.work_days:
                    raise ValidationError(_("Sorry, Employee '%s - %s' is not eligible for this Leave type") %(record.employee_id.name,record.emp_id))

                if record.employee_id and record.employee_id.date_of_joining and record.holiday_status_id.years_service and record.holiday_status_id.operators:
                    dt = record.employee_id.date_of_joining
                    d1 = datetime.strptime(dt, "%Y-%m-%d").date()
                    d2 = date.today()
                    rd = relativedelta(d2, d1)
                    work_years = int(rd.years)

                    employee_eligible = False

                    if record.holiday_status_id.operators == '=':
                        if work_years == record.holiday_status_id.years_service:
                            employee_eligible = True
                    elif record.holiday_status_id.operators == '!=':
                        if work_years != record.holiday_status_id.years_service:
                            employee_eligible = True
                    elif record.holiday_status_id.operators == '>':
                        if work_years > record.holiday_status_id.years_service:
                            employee_eligible = True
                    elif record.holiday_status_id.operators == '>=':
                        if work_years >= record.holiday_status_id.years_service:
                            employee_eligible = True
                    elif record.holiday_status_id.operators == '<':
                        if work_years < record.holiday_status_id.years_service:
                            employee_eligible = True
                    elif record.holiday_status_id.operators == '<=':
                        if work_years <= record.holiday_status_id.years_service:
                            employee_eligible = True

                    if employee_eligible != True:
                        raise ValidationError(_("Sorry, Employee '%s - %s' is not eligible for this Leave type") % (record.employee_id.name,record.emp_id))

    @api.onchange('emp_id')
    def onchange_emp_id_value(self):
        for record in self:
            if record.emp_id:
                employee = self.env['hr.employee'].search([('emp_id', '=', record.emp_id), ('active', '=', True)])
                if employee:
                    record.employee_id = employee.id
                    record._onchange_employee_id()
                    record.office_type_id = employee.unit_type_id.id
                else:
                    record.employee_id = record.office_type_id = None

    
    
    @api.onchange('employee_id','year_of_passing')
    def _onchange_employee_id(self):
        for record in self:
            record.manager_id = record.employee_id and record.employee_id.parent_id
            record.department_id = record.employee_id.department_id
            if record.employee_id and record.year_of_passing:
                leave_ids = []
                for leave_status in self.env['hr.holidays.status'].search([('office_type_id','=',record.employee_id.unit_type_id.id),
                                                                           ('entity_id','=',record.employee_id.entity_id.id),
                                                                           ('active','=',True)
                                                                           ]):
                    add_leave = 0.00
                    remove_leave = 0.00
                    for add_leaves in self.env['hr.holidays'].search([('employee_id', '=', record.employee_id.id),
                                                          ('type','=','add'),
                                                          ('state','=','validate'),
                                                          ('holiday_status_id', '=', leave_status.id),
                                                          ('year_of_passing','=',record.year_of_passing)]):
                        add_leave += add_leaves.number_of_days_temp
                    for remove_leaves in self.env['hr.holidays'].search([('employee_id', '=', record.employee_id.id),
                                                          ('type','=','remove'),
                                                          ('state','=','validate'),
                                                          ('year_of_passing','=',record.year_of_passing),
                                                          ('holiday_status_id', '=', leave_status.id)]):
                        remove_leave += remove_leaves.number_of_days_temp
                    if add_leave > remove_leave or leave_status.code in ['LWP','OD','SPL']:
                        leave_ids.append(leave_status.id)
                print (leave_ids,"wwwwwwwwwwwww")
                if record.type == 'remove':
                    #record.holiday_status_id = None
                    if record.employee_id.gender_id.name == 'Male':
                        return {'domain': {'holiday_status_id': [('gender', '!=', 'female'),('id','in',leave_ids)]}}
                    elif record.employee_id.gender_id.name == 'Female':
                        print ('aaaaaaaaaaaa')
                        return {'domain': {'holiday_status_id': [('gender', '!=', 'male'),('id','in',leave_ids)]}}
                    else:
                        return {'domain': {'holiday_status_id': [('id','in',leave_ids)]}}
    
    @api.onchange('date_from','date_to','holiday_status_id','employee_id')
    def _onchange_date_to(self):
        """ Update the number_of_days. """
        for record in self:
            leave_list = []
            number_of_days_temp = 0
            record.holiday_calendar_line = None
            if record.date_from and record.date_to and record.holiday_status_id and record.employee_id:
                holiday_status_id   = record.holiday_status_id
                per_month_days      = holiday_status_id.per_month_days
                
                calendar_line_first_date = datetime.strptime(record.date_from, "%Y-%m-%d").date()
                calendar_line_first_date = calendar_line_first_date.replace(day=1)
                calendar_line_last_date = datetime.strptime(record.date_to, "%Y-%m-%d").date()
                leave_last_date = calendar.monthrange(calendar_line_last_date.year, calendar_line_last_date.month)[1]
                leave_request_month_last_date = calendar_line_last_date.replace(day=leave_last_date)
                total_months = 0.00
                rd = relativedelta(leave_request_month_last_date,calendar_line_first_date)
                months =  rd.months
                days = rd.days
                if days:
                    total_months = months + 1
                else:
                    total_months = months
                
                if total_months:
                    per_month_days = per_month_days * total_months
                parts_of_the_day    = holiday_status_id.parts_of_the_day
                years_service  = holiday_status_id.years_service
                include_all         = holiday_status_id.include_all
                work_days           = holiday_status_id.work_days
                dates = self.generate_dates(record.date_from,record.date_to)
                
                leave_count = 0
                for daily_attendance in dates:
                    employee_eligible = False
                    operators = record.holiday_status_id.operators
                    years = record.employee_id.no_of_yrs
                    
                    if not years_service or not work_days:
                        employee_eligible = True
                    elif years_service or work_days:
                        
                        if years_service and not work_days:
                            if years and operators:
                                if operators == '=':
                                    if years == years_service:
                                        employee_eligible = True
                                elif  operators == '!=':
                                    if years != years_service:
                                        employee_eligible = True
                                elif  operators == '>':
                                    if years > years_service:
                                        employee_eligible = True
                                elif  operators == '>=':
                                    if years >= years_service:
                                        employee_eligible = True
                                elif  operators == '<':
                                    if years < years_service:
                                        employee_eligible = True
                                elif  operators == '<=':
                                    if years <= years_service:
                                        employee_eligible = True
                        elif not years_service and work_days:
                            if work_days <= record.employee_id.working_days:
                                employee_eligible = True
                        elif years_service and work_days:
                            employee_years_eligible  = False
                            employee_work_days_eligible = False 
                            if years and operators:
                                if operators == '=':
                                    if years == years_service:
                                        employee_years_eligible = True
                                elif  operators == '!=':
                                    if years != years_service:
                                        employee_years_eligible = True
                                elif  operators == '>':
                                    if years > years_service:
                                        employee_years_eligible = True
                                elif  operators == '>=':
                                    if years >= years_service:
                                        employee_years_eligible = True
                                elif  operators == '<':
                                    if years < years_service:
                                       employee_years_eligible = True
                                elif  operators == '<=':
                                    if years <= years_service:
                                       employee_years_eligible = True
                            if work_days <= record.employee_id.working_days:
                                employee_work_days_eligible = True 
                            if  employee_years_eligible and employee_work_days_eligible:
                                employee_eligible = True
                    if employee_eligible:
                        calendar_sr = self.env['hr.calendar'].search([('branch_id','=',record.employee_id.branch_id.id),
                                                                  ('state','=','approve')])
                        calendar_line_sr = self.env['hr.calendar.line'].search([('calendar_id','in', calendar_sr.ids),('date','=',daily_attendance)])
                        ('full_day','Full-Day'),('half_full_day','Half-Day or Full-Day')
                        
                        parts_of_the_day = 'half_day'
                        if record.holiday_status_id.parts_of_the_day in ['full_day','half_full_day']:
                            parts_of_the_day = 'full_day'
                        
                        if calendar_line_sr and record.holiday_status_id.code not in ['LWP','OD','SPL']:
                            if leave_count <= per_month_days and calendar_line_sr.work_type == 'work':
                                leave_list.append((0,0,{
                                                        'holidays_id'               :   record.id,
                                                        'calendar_line_id'          :   calendar_line_sr.id,
                                                        'date'                      :   calendar_line_sr.date,
                                                        'work_type'                 :   calendar_line_sr.work_type,
                                                        'include_all'               :   False,
                                                        'parts_of_the_day'          :   parts_of_the_day,
                                                        'status_parts_of_the_day'   :   record.holiday_status_id.parts_of_the_day,
                                                        'leave'                     :   True,
                                                        'status_id'                 :   record.holiday_status_id.id,
                                                        }))
                                leave_count += 1
                                if calendar_line_sr.work_type == 'half_day':
                                    number_of_days_temp += 0.5
                                else:
                                    number_of_days_temp += 1
                            elif leave_count <= per_month_days and calendar_line_sr.work_type in ['week_off','holiday'] and include_all: 
                                leave_list.append((0,0,{
                                                            'holidays_id'               :record.id,
                                                            'calendar_line_id'          :calendar_line_sr.id,
                                                            'date'                      :calendar_line_sr.date,
                                                            'work_type'                 :calendar_line_sr.work_type,
                                                            'include_all'               :True,
                                                            'parts_of_the_day'          :'full_day',
                                                            'status_parts_of_the_day'   :'full_day',
                                                            'leave'                     :True,
                                                            'status_id'                 :record.holiday_status_id.id,
                                                            }))
                                number_of_days_temp += 1
                            elif calendar_line_sr.work_type in ['week_off','holiday'] and include_all and week_off_holiday_repeat:
                                leave_list.append((0,0,{
                                                            'holidays_id'               :record.id,
                                                            'calendar_line_id'          :calendar_line_sr.id,
                                                            'date'                      :calendar_line_sr.date,
                                                            'work_type'                 :calendar_line_sr.work_type,
                                                            'include_all'               :True,
                                                            'parts_of_the_day'          :'full_day',
                                                            'status_parts_of_the_day'   :'full_day',
                                                            'leave'                     :True,
                                                            'status_id'                 :record.holiday_status_id.id,
                                                            }))
                                number_of_days_temp += 1
                            else:
                                week_off_holiday_repeat = False
                        
                        elif calendar_line_sr and record.holiday_status_id.code in ['LWP','OD','SPL']:
                            if calendar_line_sr.work_type == 'work':
                                leave_list.append((0,0,{
                                                        'holidays_id'               :record.id,
                                                        'calendar_line_id'          :calendar_line_sr.id,
                                                        'date'                      :calendar_line_sr.date,
                                                        'work_type'                 :calendar_line_sr.work_type,
                                                        'include_all'               :False,
                                                        'parts_of_the_day'          :record.holiday_status_id.parts_of_the_day,
                                                        'status_parts_of_the_day'   :record.holiday_status_id.parts_of_the_day,
                                                        'leave'                     :True,
                                                        'status_id'                 :record.holiday_status_id.id,
                                                        }))
                                leave_count += 1
                                if calendar_line_sr.work_type == 'half_day':
                                    number_of_days_temp += 0.5
                                else:
                                    number_of_days_temp += 1
                            
                            elif calendar_line_sr.work_type in ['week_off','holiday'] and include_all: 
                                leave_list.append((0,0,{
                                                            'holidays_id'                   :record.id,
                                                            'calendar_line_id'              :calendar_line_sr.id,
                                                            'date'                          :calendar_line_sr.date,
                                                            'work_type'                     :calendar_line_sr.work_type,
                                                            'include_all'                   :True,
                                                            'parts_of_the_day'              :'full_day',
                                                            'status_parts_of_the_day'       :'full_day',
                                                            'leave'                         :True,
                                                            'status_id'                     :record.holiday_status_id.id,
                                                            }))
                                number_of_days_temp += 1        
            
            record.holiday_calendar_line = leave_list
            record.number_of_days_temp = number_of_days_temp
            if record.holiday_calendar_line:
                record.date_from = record.holiday_calendar_line[0].date 
                record.date_to = record.holiday_calendar_line[-1].date
            
            
                
                
            
#         date_from = self.date_from
#         date_to = self.date_to
# 
#         # Compute and update the number of days
#         if (date_to and date_from) and (date_from <= date_to):
#             self.number_of_days_temp = self._get_number_of_days(date_from, date_to, self.employee_id.id)
#         else:
#             self.number_of_days_temp = 0

    @api.multi
    def name_get(self):
        res = []
        for leave in self:
            if leave.type == 'remove':
                if self.env.context.get('short_name'):
                    res.append((leave.id, _("%s : %.2f day(s)") % (leave.name or leave.holiday_status_id.name, leave.number_of_days_temp)))
                else:
                    res.append((leave.id, _("%s on %s : %.2f day(s)") % (leave.employee_id.name or leave.category_id.name, leave.holiday_status_id.name, leave.number_of_days_temp)))
            else:
                if leave.holiday_type == 'employee':
                    res.append((leave.id, _("%s - Allocation of %s : %.2f day(s) To %s") % (leave.year_of_passing,leave.holiday_status_id.name, leave.number_of_days_temp, leave.employee_id.name)))
                elif leave.holiday_type == 'category':
                    res.append((leave.id, _("%s - Allocation of %s : %.2f day(s) To All Employees") % (leave.year_of_passing,leave.holiday_status_id.name, leave.number_of_days_temp)))
        return res
    
    @api.multi
    def name_get(self):
        res = []
        for leave in self:
            if leave.type == 'remove':
                if self.env.context.get('short_name'):
                    res.append((leave.id, _("%s : %.2f day(s)") % (leave.name or leave.holiday_status_id.name, leave.number_of_days_temp)))
                else:
                    res.append((leave.id, _("%s on %s : %.2f day(s)") % (leave.employee_id.name or leave.category_id.name, leave.holiday_status_id.name, leave.number_of_days_temp)))
            else:
                if leave.holiday_type == 'employee':
                    res.append((leave.id, _("%s - Allocation of %s : %.2f day(s) To %s") % (leave.year_of_passing,leave.holiday_status_id.name, leave.number_of_days_temp, leave.employee_id.name)))
                elif leave.holiday_type == 'category':
                    res.append((leave.id, _("%s - Allocation of %s : %.2f day(s) To All Employees") % (leave.year_of_passing,leave.holiday_status_id.name, leave.number_of_days_temp)))
        return res
    
    
    @api.constrains('type','holiday_status_id')
    def check_lop_not_allocate(self):
        for record in self:
            if record.type == 'add' and record.holiday_status_id.code in ['LWP','OD','SPL']:
                raise ValidationError(_("Can't allocate leave for : %s")% str(record.holiday_status_id.name))
    
    @api.onchange('holiday_type')
    def onchange_holiday_type(self):
        for record in self:
            if record.holiday_type == 'category':
                record.category_id = 1

    @api.constrains('number_of_days_temp','accrued_leaves')
    def check_number_of_days_temp_zero(self):
        for record in self:
            if record.type == 'add' and record.number_of_days_temp == 0:
                raise ValidationError('Leave Allocation Duration Should not be Zero')
            if record.accrued_leaves and record.accrued_leaves < 0:
                raise ValidationError('Accrued Leaves Per Month should not be Negative')


    @api.one
    @api.multi
    def action_approve(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        
        if self.type == 'add' and self.holiday_type != 'category' and not self.from_carry_forward_leave:
            
             
            already_taken_leave = 0 
            already_allocate_leave = 0 
            for leaves in self.env['hr.holidays'].search([('employee_id', '=', self.employee_id.id),
                                                          ('type','=','remove'),
                                                          ('state','=','validate'),
                                                          ('year_of_passing','=',self.year_of_passing),
                                                          ('holiday_status_id', '=', self.holiday_status_id.id)]):
                already_taken_leave += leaves.number_of_days
            for leaves in self.env['hr.holidays'].search([('employee_id', '=', self.employee_id.id),
                                                          ('type','=','add'),
                                                          ('state','=','validate'),
                                                          ('from_carry_forward_leave','=',False),
                                                          ('year_of_passing','=',self.year_of_passing),
                                                          ('holiday_status_id', '=', self.holiday_status_id.id)]):
                already_allocate_leave += leaves.number_of_days_temp
            total_status_days =  self.number_of_days_temp + already_allocate_leave
            if total_status_days > self.holiday_status_id.max_allowed_days:
                raise UserError(_('Leave Allocation Maximum: %s')% str(self.holiday_status_id.max_allowed_days - already_allocate_leave))
        
        
        # core Code
        self._check_security_action_approve()

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state != 'confirm':
                raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))

            if holiday.double_validation:
                return holiday.write({'state': 'validate1', 'first_approver_id': current_employee.id})
            else:
                holiday.action_validate()
    
    
                
                
    @api.multi
    def action_approve1(self):
        # if double_validation: this method is the first approval approval
        # if not double_validation: this method calls action_validate() below
        self._check_security_action_approve()

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state != 'confirm':
                raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))

            if holiday.double_validation:
                return holiday.write({'state': 'validate1', 'first_approver_id': current_employee.id})
            else:
                holiday.action_validate1()
                
    @api.multi
    def action_validate1(self):
        
        
        self._check_security_action_validate()

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate1']:
                raise UserError(_('Leave request must be confirmed in order to approve it.'))
            if holiday.state == 'validate1' and not holiday.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                raise UserError(_('Only an HR Manager can apply the second approval on leave requests.'))

            holiday.write({'state': 'validate'})
            if holiday.double_validation:
                holiday.write({'second_approver_id': current_employee.id})
            else:
                holiday.write({'first_approver_id': current_employee.id})
            if holiday.holiday_type == 'employee' and holiday.type == 'remove':
                holiday._validate_leave_request()
            elif holiday.holiday_type == 'category':
                leaves = self.env['hr.holidays']
                
                year_start_date = date(int(holiday.year_of_passing), 1, 1)
                year_end_date = date(int(holiday.year_of_passing), 12, 31)
                
                # not completed 1 year
                year_of_new_joining_employees_sr = self.env['hr.employee'].search([('date_of_joining','>=',year_start_date),('date_of_joining','<=',year_end_date)])
                
                for employee in year_of_new_joining_employees_sr:
                    
                    date_of_joining = datetime.strptime(employee.date_of_joining, "%Y-%m-%d").date()
                    rd = relativedelta(year_end_date,date_of_joining)
                    months =  rd.months
                    days = rd.days
                    total_months = 0
                    if days:
                        total_months = months + 1
                    else:
                        total_months = months
                    
                     
                    values = holiday._prepare_create_by_category(employee)
                    already_allocate_leave = 0.00
                    for leaves in self.env['hr.holidays'].search([('employee_id', '=', employee.id),
                                                          ('type','=','add'),
                                                          ('state','=','validate'),
                                                          ('holiday_status_id', '=', holiday.holiday_status_id.id),
                                                          ('year_of_passing','=',holiday.year_of_passing)]):
                        already_allocate_leave += leaves.number_of_days_temp
                    number_of_days_temp = 0
                    max_allowed_days = holiday.holiday_status_id.max_allowed_days
                    per_month_max_allowed_days = max_allowed_days/12
                    available_leave = per_month_max_allowed_days * total_months
                    if already_allocate_leave and already_allocate_leave < available_leave:
                        number_of_days_remaining = available_leave - already_allocate_leave
                        if number_of_days_remaining: 
                            if holiday.number_of_days_temp > number_of_days_remaining:
                                number_of_days_temp = number_of_days_remaining
                            else:
                                number_of_days_temp = holiday.number_of_days_temp
                    elif not already_allocate_leave:
                        if holiday.number_of_days_temp > available_leave:
                            number_of_days_temp = available_leave
                        else:
                            number_of_days_temp = holiday.number_of_days_temp
                    values.update({'year_of_passing':holiday.year_of_passing,'number_of_days_temp':number_of_days_temp})
                    leaves += self.with_context(mail_notify_force_send=False).create(values)
                
                
                # 1 Year Compleletd
                employees = self.env['hr.employee'].search([('id','not in',year_of_new_joining_employees_sr.ids),('date_of_joining','<',year_start_date)])
                for employee in employees:
                    values = holiday._prepare_create_by_category(employee)
                    already_allocate_leave = 0.00
                    for leaves in self.env['hr.holidays'].search([('employee_id', '=', employee.id),
                                                          ('type','=','add'),
                                                          ('state','=','validate'),
                                                          ('holiday_status_id', '=', holiday.holiday_status_id.id),
                                                          ('year_of_passing','=',holiday.year_of_passing)]):
                        already_allocate_leave += leaves.number_of_days_temp
                    number_of_days_temp = 0
                    max_allowed_days = holiday.holiday_status_id.max_allowed_days
                    if already_allocate_leave and already_allocate_leave < max_allowed_days:
                        number_of_days_remaining = max_allowed_days - already_allocate_leave
                        if number_of_days_remaining: 
                            if holiday.number_of_days_temp > number_of_days_remaining:
                                number_of_days_temp = number_of_days_remaining
                            else:
                                number_of_days_temp = holiday.number_of_days_temp
                    elif not already_allocate_leave:
                        if holiday.number_of_days_temp > max_allowed_days:
                            number_of_days_temp = max_allowed_days
                        else:
                            number_of_days_temp = holiday.number_of_days_temp
                    values.update({'year_of_passing':holiday.year_of_passing,'number_of_days_temp':number_of_days_temp})
                    leaves += self.with_context(mail_notify_force_send=False).create(values)
                # TODO is it necessary to interleave the calls?
                
                leaves.action_approve1()
                if leaves and leaves[0].double_validation:
                    leaves.action_validate()
        return True


class LeaveRequestRemarksLine(models.Model):
    _name = 'leave.request.remarks.line'

    leave_request_id = fields.Many2one('hr.holidays', string='Leave Request ID', ondelete='cascade')
    date = fields.Datetime('Date')
    generated_by = fields.Many2one('res.users', string='Generated By')
    remarks = fields.Char('Remarks', size=50)
    state = fields.Selection([('cancel', 'Cancelled'),('refuse', 'Rejected')
                                ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft')


class LeaveRequestWizard(models.TransientModel):
    _name = 'leave.request.wizard'

    remarks = fields.Char('Remarks', size=50)
    is_cancelled = fields.Boolean('Is Cancelled')

    def action_cancel(self):
        for record in self:
            request = self.env['hr.holidays'].search([('id', '=', record.env.context.get('active_id'))])
            request.action_cancel()
            remarks_line = self.env['leave.request.remarks.line']
            remarks_line.create({
                'leave_request_id': request.id,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'generated_by': record.env.user.id,
                'remarks': record.remarks,
                'state': request.state,
            })

    def action_reject(self):
        for record in self:
            request = self.env['hr.holidays'].search([('id', '=', record.env.context.get('active_id'))])
            request.action_refuse()
            remarks_line = self.env['leave.request.remarks.line']
            remarks_line.create({
                'leave_request_id': request.id,
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'generated_by': record.env.user.id,
                'remarks': record.remarks,
                'state': request.state,
            })


# class al_lop_configuration(models.Model):
#     _name = "al.lop.configuration"
#     
#     from_days = fields.Integer('From Days')
#     to_days = fields.Integer('To Days')
#     percentage = fields.Float('Percentage (%)')
#     status_id = fields.Many2one('hr.holidays.status','Status')


   
class HrHolidaysCalendarLine(models.Model):
    _name = 'hr.holidays.calendar.line'

    holidays_id                 = fields.Many2one('hr.holidays', string='Holidays ID')
    calendar_line_id            = fields.Many2one('hr.calendar.line', String='Calendar Line')
    date                        = fields.Date(string='Date')
    work_type                   = fields.Selection([('work', 'Work Day'), ('week_off', 'Weekly-Off'), ('holiday', 'Holiday')],string="State")
    include_all                 = fields.Boolean(string='Weekly off / Holiday')
    parts_of_the_day            = fields.Selection([('half_day','Half-Day'),('full_day','Full-Day'),('half_full_day','Half-Day or Full-Day')])
    leave                       = fields.Boolean(string='Leave')
    status_id                   = fields.Many2one('hr.holidays.status', string='Status')
    status_parts_of_the_day     = fields.Selection([('half_day','Half-Day'),('full_day','Full-Day'),('half_full_day','Half-Day or Full-Day')])
    
class HrPayslip(models.Model):
    _inherit = "hr.payslip"
    
    @api.multi
    def alllowance_and_deduction(self):
        all_list = []
        for record in self:
            
            alw_total_ids = []
            
            for line_one in record.line_ids:
                if (line_one.category_id.name == 'Allowance') or (line_one.category_id.code == 'BASIC') and line_one.salary_rule_id.appears_on_payslip and line_one.total:
                    alw_total_ids.append(line_one.id)
                    
                    
            ded_total_ids = []
            for line_two in record.line_ids:
                if (line_two.category_id.name == 'Deduction') or (line_two.category_id.code == 'LOP') and line_two.salary_rule_id.appears_on_payslip and line_two.total:
                    ded_total_ids.append(line_two.id)
            
            list_length = alw_total_ids + ded_total_ids
            
            all_ded_ids = []
            
            for list_len in list_length:
                
                alw_name = ''
                alw_code = ''
                alw_amount = 0.00
                ded_name = ''
                ded_code = ''
                ded_amount = 0.00
                
                alw = False
                for line in record.line_ids:
                    if (line.category_id.name == 'Allowance' or line.category_id.code == 'BASIC') and line.id not in all_ded_ids and line.id in alw_total_ids and line.salary_rule_id.appears_on_payslip and line.total:
                        all_ded_ids.append(line.id)
                        alw_name = line.name
                        alw_code = line.code
                        alw_amount = line.total
                        alw = True
                        break
                ded = False
                for line in record.line_ids:
                    if (line.category_id.name == 'Deduction' or line.category_id.code == 'LOP') and not line.code in ['epfer','EPFER'] and line.id not in all_ded_ids and line.id in ded_total_ids and line.salary_rule_id.appears_on_payslip and line.total:
                        all_ded_ids.append(line.id)
                        ded_name = line.name
                        ded_code = line.code
                        ded_amount = abs(line.total)
                        ded = True
                        break
                if alw or ded:
                    all_list.append({
                        'alw_name' : alw_name,
                        'alw_code' : alw_code,
                        'alw_amount' : alw_amount if alw_amount else ' ',
                        'ded_name' : ded_name,
                        'ded_code' : ded_code,
                        'ded_amount' : ded_amount if ded_amount else ' ',
                        
                        })
        return all_list
    
    
    
                
class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    remaining_leaves = fields.Float(compute='_compute_leaves_count', string='Remaining Legal Leaves')
    
    @api.multi
    def _compute_leaves_count(self):
        
        for record in self:
            already_allocate_leave = 0.00
            already_taken_leave = 0.00
            for holiday_status_id in self.env['hr.holidays.status'].search([('active','=',True)]):
                for leaves in self.env['hr.holidays'].search([('employee_id', '=', record.id),
                                                      ('type','=','add'),
                                                      ('state','=','validate'),
                                                      ('to_carry_forward_leave','=',False),
                                                      ('holiday_status_id', '=', holiday_status_id.id)]):
                    if leaves.to_carry_forward_leave:
                        for line in leaves.to_carry_forward_leave.lines:
                            if line.holiday_status_id.code == holiday_status_id.code:
                                already_allocate_leave += leaves.number_of_days_temp - line.leave_balance
                    if leaves.encashment_leave:
                        for line in leaves.encashment_leave.lines:
                            if line.holiday_status_id.code == holiday_status_id.code:
                                already_allocate_leave += leaves.number_of_days_temp - line.leave_balance
                    else:
                        already_allocate_leave += leaves.number_of_days_temp
            for leave_taken in self.env['hr.holidays'].search([('employee_id', '=', record.id),
                                                  ('type','=','remove'),
                                                  ('state','=','validate'),
                                                  ('holiday_status_id.code', 'not in', ['LWP','OD','SPL'])]):
                
                already_taken_leave += leave_taken.number_of_days_temp
                
            record.leaves_count = already_allocate_leave - already_taken_leave
            record.remaining_leaves = already_allocate_leave - already_taken_leave
        
