from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil import parser
from dateutil.relativedelta import relativedelta
import math
import logging
import threading

_logger = logging.getLogger(__name__)



class PappayaDailyAttendance(models.Model):
    _name = 'hr.daily.attendance'

    def get_daily_attendance_name(self):
        for record in self:
            date = parser.parse(record.attendance_date)
            proper_date = date.strftime('%d-%m-%Y')
            record.name = ('%s - %s') %(proper_date, record.branch_id.name)

    name = fields.Char('Name', compute='get_daily_attendance_name')
    company_id = fields.Many2one('res.company',string='Organization',default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('operating.unit', string='Branch',domain=[('type','=','branch')])
    attendance_date = fields.Date('Attendance Date', default=fields.Datetime.now)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'),
                              ], string='Status', readonly=True, track_visibility='onchange', copy=False,default='draft')
    daily_attendance_line = fields.One2many('hr.daily.attendance.line', 'daily_attendance_id', string='Manual Attendance Line')

    
    @api.multi
    def generate_dates(self, date_from, date_to):
        dates = []
        td = timedelta(hours=24)
        current_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        while current_date <= datetime.strptime(date_to, "%Y-%m-%d").date():
            dates.append(current_date)
            current_date += td
        return dates
    
    @api.multi
    def schedule_month_attendance_creation_branch_wise(self):
        _logger.info("Attendance Generation Process Start")
        today = datetime.now().date()
        month_start_date = today.replace(day=1)
        hr_daily_attendance_obj = self.env['hr.daily.attendance']
        for attendance_date in self.generate_dates(str(month_start_date),str(today)):
            for branch in self.env['operating.unit'].search([('type','=','branch')]):
                hr_daily_attendance_sr = hr_daily_attendance_obj.search([('branch_id','=',branch.id),('attendance_date','=',attendance_date)])
                if not hr_daily_attendance_sr:
                    hr_attendance = hr_daily_attendance_obj.create({'branch_id':branch.id,'attendance_date':attendance_date})
                    hr_attendance.onchnage_branch_id()
                    _logger.info("Attendance Generation Process Branch :%s and Attendance Date: %s", branch.name,str(attendance_date))
        _logger.info("Attendance Generation Process End")
            
            
    @api.multi
    def schedule_month_attendance_update(self):
        _logger.info("Attendance Update Process Start")
        today = datetime.now().date()
        month_start_date = today.replace(day=1)
        hr_daily_attendance_obj = self.env['hr.daily.attendance']
        attendance_update = hr_daily_attendance_obj.search([('attendance_date','>=',month_start_date),('attendance_date','<=',today),('state','=','draft')])
        for attendance in attendance_update:
            attendance.attendance_update()
        _logger.info("Attendance Update Process End")
            
            
    @api.multi
    def schedule_today_attendance_creation_branch_wise(self):
        _logger.info("Attendance Generation Process Start")
        today = datetime.now().date()
        hr_daily_attendance_obj = self.env['hr.daily.attendance']
        attendance_date = str(today)
        for branch in self.env['operating.unit'].search([('type','=','branch')]):
            hr_daily_attendance_sr = hr_daily_attendance_obj.search([('branch_id','=',branch.id),('attendance_date','=',attendance_date)])
            if not hr_daily_attendance_sr:
                hr_attendance = hr_daily_attendance_obj.create({'branch_id':branch.id,'attendance_date':attendance_date})
                hr_attendance.onchnage_branch_id()
                _logger.info("Attendance Generation Process Branch :%s and Attendance Date: %s", branch.name,str(attendance_date))
        _logger.info("Attendance Generation Process End")
            
            
    @api.multi
    def schedule_today_attendance_update(self):
        _logger.info("Attendance Update Process Start")
        today = datetime.now().date()
        hr_daily_attendance_obj = self.env['hr.daily.attendance']
        attendance_update = hr_daily_attendance_obj.search([('attendance_date','=',today),('state','=','draft')])
        for attendance in attendance_update:
            attendance.attendance_update()
        _logger.info("Attendance Update Process End")
        
        
        
    
        
    @api.multi
    def daily_attendance_create_and_update_one(self):
        self.env.cr.execute(""" 
                            CREATE OR REPLACE FUNCTION GetWorkHoursManual(checkintime timestamp  , chekouttime timestamp , statrtime float, startduration character varying, endtime float, endDuration character varying, branchId integer) RETURNS float AS $$
                            DECLARE
                            consideredCheckinTime TIMESTAMP;
                            consideredCheckoutTime TIMESTAMP;
                            --returnRecord workingHoursType; 
                            workingHours  character varying;
                            tempWorkHours TIMESTAMP;
                            --presentStatus character varying;
                            BEGIN
                                  IF checkInTime IS NULL OR chekOutTime IS NULL THEN 
                                     return 0.0;  
                                  ELSE
                                       --RAISE NOTICE 'checkInTime  (%)', (checkInTime + interval '5 hour') + interval '30 minute'  ;
                                       --RAISE NOTICE 'configured Time (start)  (%)', concat(to_char(checkInTime ,'YYYY-MM-DD'),' ', statrTime , ':00:00 ' , startDuration):: timestamp;
                                  
                                      IF (checkInTime + interval '5 hour') + interval '30 minute' > concat(to_char(checkInTime ,'YYYY-MM-DD'),' ', statrTime , ':00:00 ' , startDuration):: timestamp THEN
                                        
                                          consideredCheckinTime  = (checkInTime + interval '5 hour') + interval '30 minute';
                                      ELSE 
                                         consideredCheckinTime   = concat(to_char(checkInTime ,'YYYY-MM-DD') ,' ', statrTime , ':00:00 ' , startDuration):: timestamp;  
                                      END IF; 
                            
                                      IF (chekOutTime + interval '5 hour') + interval '30 minute'< concat(to_char(chekOutTime ,'YYYY-MM-DD') , ' ',endTime , ':00:00 ' , endDuration):: timestamp THEN
                                        
                                          consideredCheckoutTime = (chekOutTime  + interval '5 hour') + interval '30 minute' ;
                                      ELSE 
                                         consideredCheckoutTime = concat(to_char(chekOutTime ,'YYYY-MM-DD') ,' ', endTime , ':00:00 ' , endDuration):: timestamp;  
                                      END IF;
                                          
                                      --RAISE NOTICE 'Considered In Time (%)', consideredCheckinTime   ;
                                      --RAISE NOTICE 'Considered out Time (%)', consideredCheckoutTime ;  
                            
                                     -- workingHours =  (EXTRACT(EPOCH FROM consideredCheckoutTime  ) - EXTRACT(EPOCH FROM consideredCheckinTime ))/3600 ;
                                      workingHours  = age(consideredCheckoutTime, consideredCheckinTime );
                            
                                     tempWorkHours =  concat(to_char(checkInTime ,'YYYY-MM-DD'),' ', workingHours ):: timestamp ;
                            
                                      --RAISE NOTICE 'workingHours  (%)', to_char(tempWorkHours ,'HH.MI') ;  
                                  END IF;  
                                  return cast (to_char(tempWorkHours ,'HH24.MI') as float);
                            END;
                            $$ LANGUAGE PLPGSQL;
        
                            """)
        
        
        self.env.cr.execute(""" 
                            CREATE OR REPLACE FUNCTION GetWorkHours(checkintime timestamp  , chekouttime timestamp , statrtime float, startduration character varying, endtime float, endDuration character varying, branchId integer) RETURNS float AS $$
                            DECLARE
                            consideredCheckinTime TIMESTAMP;
                            consideredCheckoutTime TIMESTAMP;
                            --returnRecord workingHoursType; 
                            workingHours  character varying;
                            tempWorkHours TIMESTAMP;
                            --presentStatus character varying;
                            BEGIN
                                  IF checkInTime IS NULL OR chekOutTime IS NULL THEN 
                                     return 0.0;  
                                  ELSE
                                       RAISE NOTICE 'checkInTime  (%)', checkInTime   ;
                                       RAISE NOTICE 'configured Time (start)  (%)', concat(to_char(checkInTime ,'YYYY-MM-DD'),' ', statrTime , ':00:00 ' , startDuration):: timestamp;
                                  
                                      IF ( checkInTime  > concat(to_char(checkInTime ,'YYYY-MM-DD'),' ', statrTime , ':00:00 ' , startDuration):: timestamp ) THEN
                                        
                                          consideredCheckinTime  = checkInTime ;
                                      ELSE 
                                         consideredCheckinTime   = concat(to_char(checkInTime ,'YYYY-MM-DD') ,' ', statrTime , ':00:00 ' , startDuration):: timestamp;  
                                      END IF; 
                            
                                      IF (chekOutTime < concat(to_char(chekOutTime ,'YYYY-MM-DD') , ' ',endTime , ':00:00 ' , endDuration):: timestamp ) THEN
                                        
                                          consideredCheckoutTime = chekOutTime   ;
                                      ELSE 
                                         consideredCheckoutTime = concat(to_char(chekOutTime ,'YYYY-MM-DD') ,' ', endTime , ':00:00 ' , endDuration):: timestamp;  
                                      END IF;
                                          
                                      RAISE NOTICE 'Considered In Time (%)', consideredCheckinTime   ;
                                      RAISE NOTICE 'Considered out Time (%)', consideredCheckoutTime ;  
                            
                                     -- workingHours =  (EXTRACT(EPOCH FROM consideredCheckoutTime  ) - EXTRACT(EPOCH FROM consideredCheckinTime ))/3600 ;
                                      workingHours  = age(consideredCheckoutTime, consideredCheckinTime );
                            
                                     tempWorkHours =  concat(to_char(checkInTime ,'YYYY-MM-DD'),' ', workingHours ):: timestamp ;
                            
                                      RAISE NOTICE 'workingHours  (%)', to_char(tempWorkHours ,'HH24.MI') ;  
                                  END IF;  
                                  return cast (to_char(tempWorkHours ,'HH24.MI') as float);
                            END;
                            $$ LANGUAGE PLPGSQL;
        
                            """)
    
    @api.multi
    def daily_attendance_create_and_update_two(self):
        self.env.cr.execute(""" 
                            CREATE OR REPLACE FUNCTION create_attendance_lines()
                                       RETURNS text AS $$
                                            DECLARE  
                                              cur_branch RECORD;
                                              cur_employee RECORD;
                                              branch_work_hours RECORD;
                                              attendance_row_id INTEGER;
                                              attendance_count  INTEGER;
                                              employee_check_in Timestamp;
                                              employee_check_out Timestamp;
                                              v_daily_attendance_id INTEGER;
                                              workHours float;
                                              presentStatus character varying;
                                              DateAttendance DATE;
                                            
                                              employee_attendance_line_count INTEGER;
                                              branch_cursor CURSOR  FOR select * from operating_unit where type = 'branch';
                                              employee_cursor CURSOR (branchid INTEGER) FOR select id, unique_id from hr_employee where branch_id =  branchid;
                                            BEGIN
                                               -- Open the cursor
                                               OPEN branch_cursor ;
                                                
                                               LOOP
                                                  DateAttendance = now()::date;
                                                  attendance_count =0;
                                                -- fetch row into the film
                                                  FETCH branch_cursor INTO cur_branch ;
                                                -- exit when no more row to fetch
                                                  EXIT WHEN NOT FOUND;
                                            
                                                  BEGIN 
                                                  
                                                  select count(1) INTO attendance_count from hr_daily_attendance where branch_id = cur_branch.id and  attendance_date = DateAttendance;
                                                  
                                                  IF  attendance_count > 0 THEN
                                                    select id  INTO attendance_row_id from hr_daily_attendance  where branch_id = cur_branch.id and  attendance_date = DateAttendance;
                                                  
                                                  ELSE
                                                    select COALESCE (max(id + 1 ),1) INTO attendance_row_id from hr_daily_attendance ;
                                                    insert into hr_daily_attendance (id, branch_id, attendance_date,state) values (attendance_row_id ,cur_branch.id, DateAttendance,'draft');
                                            
                                                  END IF;
                                                  END;
                                                  OPEN employee_cursor (cur_branch.id);
                                                  LOOP 
                                                         employee_attendance_line_count=0;
                                                         employee_check_out = NULL;
                                                         employee_check_in = NULL;
                                                         FETCH employee_cursor  INTO cur_employee ; 
                                                         EXIT WHEN NOT FOUND;
                                                         select (CASE WHEN event_time::date = DateAttendance  THEN event_time END) INTO  employee_check_in from attendance_history_table WHERE userid1 = cur_employee.unique_id::BIGINT and event_dt = DateAttendance ORDER BY event_time asc limit 1;
                                                         select (CASE WHEN event_time::date = DateAttendance  THEN event_time END) INTO  employee_check_out from attendance_history_table WHERE userid1 = cur_employee.unique_id::BIGINT and event_dt = DateAttendance ORDER BY event_time desc limit 1;
                                                         select id INTO employee_attendance_line_count from hr_daily_attendance_line  where employee_id =  cur_employee.id and daily_attendance_id  = attendance_row_id ;
        
                                                        IF (employee_check_in  = employee_check_out) THEN
                                                        employee_check_out = null;
                                                        ELSE

select * from branch_officetype_workhours_line  into branch_work_hours where branch_id = cur_branch.id and employee_type = cur_employee.employee_type  limit 1;

IF(branch_work_hours  IS NULL ) THEN
        select * from branch_officetype_workhours_line  into branch_work_hours where branch_id = cur_branch.id   limit 1;
END IF;
                                                                                                         select GetWorkHours(employee_check_in , employee_check_out,branch_work_hours.start_time,branch_work_hours.start_duration,branch_work_hours.end_time,branch_work_hours.end_duration, cur_branch.ID ) into workHours ;
                                                        END IF;
        
        
        
                    
                                                         IF workHours  <= 0 THEN
                                                                   presentStatus  = 'absent';
                                                         ELSE
                                                                    select COALESCE(status_type,'absent') into presentStatus from branch_officetype_workhours_line where branch_id = cur_branch.id and  workHours  >= min_work_hours and workHours <= max_work_hours  and employee_type = cur_employee.employee_type  limit 1;             
                                                         END IF;
                                                         BEGIN
                                                         IF employee_attendance_line_count > 0  THEN
                                                                update hr_daily_attendance_line  set check_in = employee_check_in , check_out = employee_check_out, worked_hours= workHours , attendance_status = presentStatus, attendance_type='card_entry'   where id =  employee_attendance_line_count and attendance_type != 'manual';             
                                                         ELSE
                                                                select COALESCE (max(id + 1 ),1) into v_daily_attendance_id from hr_daily_attendance_line  ;
                                                                INSERT INTO hr_daily_attendance_line  (id,employee_id,attendance_date,biometric_id, check_in, check_out, daily_attendance_id,state,worked_hours,attendance_status,attendance_type ) values ( v_daily_attendance_id , cur_employee.id, DateAttendance, cur_employee.unique_id, 
                                                                       employee_check_in , employee_check_out, attendance_row_id , 'draft',workHours , presentStatus,'card_entry' );  
                                            
                                                         END IF;
                                                         END;                      
                                               END LOOP;
                                               CLOSE employee_cursor ;
                                               END LOOP;
                                               -- Close the cursor
                                               CLOSE branch_cursor ;
                                               PERFORM setval('hr_daily_attendance_id_seq', COALESCE((SELECT MAX(id)+1 FROM hr_daily_attendance), 1), false);
                                               PERFORM setval('hr_daily_attendance_line_id_seq', COALESCE((SELECT MAX(id)+1 FROM hr_daily_attendance_line), 1), false);
                                               RETURN 0;
                                            END;
                                    $$ 
                                    LANGUAGE plpgsql;
                            """)
    
    
    def daily_attendance_create_and_update_main(self):
        self.env.cr.execute("""select create_attendance_lines();""")
    
    def daily_attendance_create_and_update_final(self):
        self.daily_attendance_create_and_update_main()
        return True
    
    @api.multi
    def Branch_wise_attendance_update(self):
        self.env.cr.execute(""" 
                            CREATE OR REPLACE FUNCTION Branch_wise_attendance_update(BranchID INTEGER,DateAttendance VARCHAR)
                                       RETURNS text AS $$
                                        DECLARE  
                                          cur_branch RECORD;
                                          cur_employee RECORD;
                                          attendance_row_id INTEGER;
                                          attendance_count  INTEGER;
                                          employee_check_in Timestamp;
                                          employee_check_out Timestamp;
                                          v_daily_attendance_id INTEGER;
                                          workHours float;
                                          presentStatus character varying;
                                        
                                        
                                          employee_attendance_line_count INTEGER;
                                          branch_cursor CURSOR  FOR select * from operating_unit where type = 'branch' and id= BranchID;
                                          employee_cursor CURSOR (branchid INTEGER) FOR select id, unique_id,employee_type from hr_employee where branch_id =  branchid;
                                        BEGIN
                                           -- Open the cursor
                                           OPEN branch_cursor ;
                                            
                                           LOOP
                                              attendance_count = 0;
                                            -- fetch row into the film
                                              FETCH branch_cursor INTO cur_branch ;
                                            -- exit when no more row to fetch
                                              EXIT WHEN NOT FOUND;
                                        
                                              BEGIN 
                                              
                                              select count(1) INTO attendance_count from hr_daily_attendance where branch_id = cur_branch.id and  attendance_date = DateAttendance::date;
                                              
                                              IF  attendance_count > 0 THEN
                                                select id  INTO attendance_row_id from hr_daily_attendance  where branch_id = cur_branch.id and  attendance_date = DateAttendance::date;
                                              
                                              ELSE
                                                select COALESCE (max(id + 1 ),1) INTO attendance_row_id from hr_daily_attendance ;
                                                insert into hr_daily_attendance (id, branch_id, attendance_date,state) values (attendance_row_id ,cur_branch.id, DateAttendance::date,'draft');
                                        
                                              END IF;
                                              END;
                                              OPEN employee_cursor (cur_branch.id);
                                              LOOP 
                                                     employee_attendance_line_count=0;
                                                     employee_check_out = NULL;
                                                     employee_check_in = NULL;
                                                     FETCH employee_cursor  INTO cur_employee ; 
                                                     EXIT WHEN NOT FOUND;
                                                     select (CASE WHEN event_time::date = DateAttendance::date  THEN event_time END)  INTO  employee_check_in from attendance_history_table WHERE userid1 = cur_employee.unique_id::BIGINT and event_dt = DateAttendance::date ORDER BY event_time asc limit 1;
                                                     select (CASE WHEN event_time::date = DateAttendance::date  THEN event_time END) INTO  employee_check_out from attendance_history_table WHERE userid1 = cur_employee.unique_id::BIGINT and event_dt = DateAttendance::date ORDER BY event_time desc limit 1;
                                                     select id INTO employee_attendance_line_count from hr_daily_attendance_line  where employee_id =  cur_employee.id and daily_attendance_id  = attendance_row_id ;
                                                    
                                                    --RAISE NOTICE 'employee_check_in employee_check_out DateAttendance (%%%%%)', (employee_check_in,employee_check_out,DateAttendance,employee_check_in::date,employee_check_out::date) ;
                                                    IF (employee_check_in  = employee_check_out) THEN
                                                    employee_check_out = null;
                                                    ELSE
                                                                                                     select GetWorkHours(employee_check_in , employee_check_out,cur_branch.start_time,cur_branch.start_duration,cur_branch.end_time,cur_branch.end_duration, cur_branch.ID ) into workHours ;
                                                    END IF;
    
    
    
                
                                                     IF workHours  <= 0 THEN
                                                               presentStatus  = 'absent';
                                                     ELSE
                                                                select COALESCE(status_type,'absent') into presentStatus from branch_officetype_workhours_line where branch_id = cur_branch.id and  workHours  >= min_work_hours and workHours <= max_work_hours  and employee_type = cur_employee.employee_type  limit 1;             
                                                     END IF;
                                                     BEGIN
                                                     IF employee_attendance_line_count > 0  THEN
                                                            update hr_daily_attendance_line  set check_in = employee_check_in , check_out = employee_check_out, worked_hours= workHours , attendance_status = presentStatus, attendance_type='card_entry'   where id =  employee_attendance_line_count and attendance_type != 'manual';             
                                                     ELSE
                                                            select COALESCE (max(id + 1 ),1) into v_daily_attendance_id from hr_daily_attendance_line  ;
                                                            INSERT INTO hr_daily_attendance_line  (id,employee_id,attendance_date,biometric_id, check_in, check_out, daily_attendance_id,state,worked_hours,attendance_status,attendance_type ) values ( v_daily_attendance_id , cur_employee.id, DateAttendance::date, cur_employee.unique_id, 
                                                                   employee_check_in , employee_check_out, attendance_row_id , 'draft',workHours , presentStatus,'card_entry' );  
                                        
                                                     END IF;
                                                     END;                      
                                           END LOOP;
                                           CLOSE employee_cursor ;
                                           END LOOP;
                                           -- Close the cursor
                                           CLOSE branch_cursor ;
                                           PERFORM setval('hr_daily_attendance_id_seq', COALESCE((SELECT MAX(id)+1 FROM hr_daily_attendance), 1), false);
                                           PERFORM setval('hr_daily_attendance_line_id_seq', COALESCE((SELECT MAX(id)+1 FROM hr_daily_attendance_line), 1), false);
                                           RETURN 0;
                                        END;
                                    $$ 
                                    LANGUAGE plpgsql;
                                        """)
    
    
    @api.multi
    def attendance_update(self):
        self.Branch_wise_attendance_update()
        self.env.cr.execute("""select Branch_wise_attendance_update(%s,%s);""",(self.branch_id.id,self.attendance_date))
        print ("sucesss")
        
    @api.multi
    def attendance_create_branch_and_date_range(self,branch_id,date_from,date_to):
        if branch_id and date_from and date_to:
            #self.Branch_wise_attendance_update()
            dates = self.generate_dates(date_from, date_to)
            for attendance_date in dates:
                self.env.cr.execute("""select Branch_wise_attendance_update(%s,%s);""",(branch_id,str(attendance_date)))
                print ("sucesss")
        
        if not branch_id and date_from and date_to:
            #self.Branch_wise_attendance_update()
            dates = self.generate_dates(date_from, date_to)
            for branch_id in self.env['operating.unit'].search([('type','=','branch')]):
                for attendance_date in dates:
                    print (branch_id.id,str(attendance_date),"3edddddddddddddddddddddddddd")
                    self.env.cr.execute("""select Branch_wise_attendance_update(%s,%s);""",(branch_id.id,str(attendance_date)))
                    print ("sucesss")


        # Old logic code
#     @api.multi
#     def attendance_update(self):
#         for record in self:
#             daily_attendance_line = []
#             employees = self.env['hr.employee'].search([('branch_id','=',record.branch_id.id),('active','=', True),('id','!=',1)])
#             for employee in employees:
#                 exit = record.daily_attendance_line.search([('daily_attendance_id','=',record.id),('employee_id','=',employee.id)])
#                 if exit and employee.unique_id and record.attendance_date:
#                     self.env.cr.execute("""select * from attendance_history_table WHERE userid = %s and event_dt = %s ORDER BY id""", (employee.unique_id,record.attendance_date))
#                     employee_attendance = self.env.cr.fetchall()
#                     if employee_attendance:
#                         if not exit.check_in and employee_attendance[0]:
#                             exit.check_in = employee_attendance[0][3]
#                             _logger.info("Attendance Update Employee :%s and Check IN: %s", employee.name,str(employee_attendance[0][3]))
#                         if employee_attendance[-1]:
#                             if employee_attendance[-1][3] and employee_attendance[-1][3] != exit.check_out and employee_attendance[0][3] != employee_attendance[-1][3]:
#                                 exit.check_out = employee_attendance[-1][3]
#                                 _logger.info("Attendance Update Employee :%s and Check OUT: %s", employee.name,str(employee_attendance[-1][3]))
#                 if not exit:
#                     last_check_in   = None
#                     last_check_out  = None
#                     if employee.unique_id and record.attendance_date:
#                         self.env.cr.execute("""select * from attendance_history_table WHERE userid = %s and event_dt = %s ORDER BY id""", (employee.unique_id,record.attendance_date))
#                         employee_attendance = self.env.cr.fetchall()
#                         if employee_attendance:
#                             status = 'absent'
#                             if employee_attendance[0]:
#                                 last_check_in = employee_attendance[0][3]
#                                 status = 'present'
#                                 _logger.info("Attendance Insert Employee :%s and Check IN: %s", employee.name,str(employee_attendance[0][3]))
#                             if employee_attendance[-1] and employee_attendance[0][3] != employee_attendance[-1][3]:
#                                 last_check_out = employee_attendance[-1][3]
#                                 status = 'present'
#                                 _logger.info("Attendance Insert Employee :%s and Check OUT: %s", employee.name,str(employee_attendance[-1][3]))
#                             daily_attendance_line.append((0, 0, {
#                                 'employee_id'       : employee.id,
#                                 'attendance_date'   : record.attendance_date,
#                                 'biometric_id'      : employee.unique_id,
#                                 'check_in'          : last_check_in,
#                                 'check_out'         : last_check_out,
#                                 'attendance_status' : status,
#                                 'state'             : 'draft',
#                             }))
#                     else:
#                         daily_attendance_line.append((0, 0, {
#                             'employee_id'       : employee.id,
#                             'attendance_date'   : record.attendance_date,
#                             'biometric_id'      : employee.unique_id,
#                             'check_in'          : last_check_in,
#                             'check_out'         : last_check_out,
#                             'attendance_status' : 'absent',
#                             'state'             : 'draft',
#                         }))
#             if daily_attendance_line:
#                 record.daily_attendance_line = daily_attendance_line        
    
    
    @api.onchange('branch_id','attendance_date')
    def onchnage_branch_id(self):
        for record in self:
            if record.branch_id and record.attendance_date:
                    employees = self.env['hr.employee'].search([('branch_id','=',record.branch_id.id),('active','=', True),('id','!=',1)])
                    print ("ddddddddddddddddddd",employees)
                    daily_attendance_line = []
                    for employee in employees:
                        last_check_in   = None
                        last_check_out  = None
                        # if employee.unique_id and record.attendance_date:
                        #     self.env.cr.execute("""select * from attendance_history_table WHERE userid = %s and event_dt = %s ORDER BY id""", (employee.unique_id,record.attendance_date))
                        #     employee_attendance = self.env.cr.fetchall()
                        #     if employee_attendance:
                        #         status = 'absent'
                        #         if employee_attendance[0]:
                        #             last_check_in = employee_attendance[0][3]
                        #             status = 'present'
                        #             _logger.info("Attendance Insert Employee :%s and Check IN: %s", employee.name,str(employee_attendance[0][3]))
                        #         if employee_attendance[-1] and employee_attendance[0][3] != employee_attendance[-1][3]:
                        #             last_check_out = employee_attendance[-1][3]
                        #             status = 'present'
                        #             _logger.info("Attendance Insert Employee :%s and Check OUT: %s", employee.name,str(employee_attendance[-1][3]))
                        #         daily_attendance_line.append((0, 0, {
                        #             'employee_id'       : employee.id,
                        #             'attendance_date'   : record.attendance_date,
                        #             'biometric_id'      : employee.unique_id,
                        #             'check_in'          : last_check_in,
                        #             'check_out'         : last_check_out,
                        #             'attendance_status' : status,
                        #             'state'             : 'draft',
                        #         }))
                        # else:
                        daily_attendance_line.append((0, 0, {
                            'employee_id'       : employee.id,
                            'attendance_date'   : record.attendance_date,
                            'biometric_id'      : employee.unique_id,
                            'check_in'          : last_check_in,
                            'check_out'         : last_check_out,
                            'attendance_status' : 'absent',
                            'state'             : 'draft',
                        }))
                    record.daily_attendance_line = daily_attendance_line

    @api.multi
    @api.constrains('attendance_date')
    def check_date(self):
        for record in self:
            if datetime.strptime(record.attendance_date, DEFAULT_SERVER_DATE_FORMAT).date() > datetime.now().date():
                raise ValidationError('Please check future date not allowed')

    @api.multi
    def attendance_confirm(self):
        for record in self:
            for line in record.daily_attendance_line:
                attendance = self.env['hr.attendance'].search([('employee_id', '=', line.employee_id.id), ('attendance_date', '=', record.attendance_date)])
                attendance.write({'state': 'done'})
                line.write({'state': 'done'})
            record.write({'state': 'done'})

    @api.multi
    def attendance_reset(self):
        for record in self:
            for line in record.daily_attendance_line:
                attendance = self.env['hr.attendance'].search([('employee_id', '=', line.employee_id.id), ('attendance_date', '=', record.attendance_date)])
                attendance.write({'state': 'draft'})
                line.write({'state': 'draft'})
            record.write({'state': 'draft'})

    @api.constrains('branch_id', 'attendance_date')
    def check_branch_attendance_date(self):
        if len(self.search([('branch_id', '=', self.branch_id.id), ('attendance_date', '=', self.attendance_date)])) > 1:
            raise ValidationError("Record already exists for this Attendance Date")


class PappayaDailyAttendanceLine(models.Model):
    _name = 'hr.daily.attendance.line'

    
    @api.onchange('check_in', 'check_out')
    def onchnage_check_in_check_out(self):
        for record in self:
            record.attendance_type = 'manual'
            status_type_id = self.env['branch.officetype.workhours.line'].search([('branch_id','=',record.employee_id.branch_id.id),
                                                                                  ('min_work_hours','<=',record.worked_hours),
                                                                                  ('max_work_hours','>=',record.worked_hours)],limit=1)
            if record.check_out and record.check_in and not record.check_out < record.check_in:
                if status_type_id:
                    record.attendance_status = status_type_id.status_type
                else:
                    record.attendance_status = 'absent'
            else:
                record.attendance_status = 'absent'
    
    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                if not attendance.check_out < attendance.check_in and attendance.attendance_date == attendance.check_in[0:10] and attendance.attendance_date == attendance.check_out[0:10]:
                    if attendance.attendance_type == 'manual':
                        #attendance.daily_attendance_id.daily_attendance_create_and_update_one()
                       
                        time_lines = []
                        time_lines = self.env['branch.officetype.workhours.line'].search([('employee_type','=',attendance.employee_id.employee_type.id),
                                                                                          ('branch_id','=',attendance.employee_id.branch_id.id)],limit=1)
                        if not time_lines:
                            time_lines = self.env['branch.officetype.workhours.line'].search([('branch_id','=',attendance.employee_id.branch_id.id)],limit=1)
                        
                        start_time      = time_lines.start_time 
                        end_time        = time_lines.end_time
                        start_duration  = time_lines.start_duration
                        end_duration    = time_lines.end_duration
                        
                        self.env.cr.execute("""
                                            select GetWorkHoursManual(%s,%s,%s,%s,%s,%s, %s );""",(attendance.check_in,attendance.check_out,start_time,start_duration, end_time,end_duration,attendance.employee_id.branch_id.id))
                        workHours = self.env.cr.fetchall()
                        print (workHours,"workHoursworkHoursworkHoursworkHours")
                        if workHours:
                            attendance.worked_hours = workHours[0][0]
                        else:
                            attendance.worked_hours = 0.00
                    
    @api.constrains('check_in', 'check_out')
    def _check_validity_check_in_check_out(self):
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                if attendance.check_out < attendance.check_in:
                    raise ValidationError(_('"Check Out" time cannot be earlier than "Check In" time.'))
            if attendance.attendance_type == 'manual':
                if attendance.check_in:
                    if attendance.attendance_date != attendance.check_in[0:10]: 
                        raise ValidationError(_(' "Check In" Date should be equal to current Attendance Date.'))
                if attendance.check_out:
                    if attendance.attendance_date != attendance.check_out[0:10]:
                        raise ValidationError(_(' "Check Out" Date should be equal to current Attendance Date.'))
                    
                

    daily_attendance_id = fields.Many2one('hr.daily.attendance',ondelete='cascade')
    attendance_date     = fields.Date('Attendance Date')
    employee_id         = fields.Many2one('hr.employee', string='Employee Name')
    employee_code       = fields.Char(related='employee_id.emp_id', string='Employee ID')
    biometric_id        = fields.Char('Biometric ID',size=20)
    check_in            = fields.Datetime(string="Check In")
    check_out           = fields.Datetime(string="Check Out")
    worked_hours        = fields.Float(string='Worked Hours', compute='_compute_worked_hours', store=True, readonly=True)
    attendance_status   = fields.Selection([('present', 'Present'),('partial','Partial Present'),('absent', 'Absent')], string='Attendance Status')
    original_status     = fields.Selection([('present', 'Present'),('partial','Partial Present'),('absent', 'Absent')], string='Status')
    attendance_type     = fields.Selection([('card_entry', 'Card Entry'),('manual','Manual')], string='Attendance Type',default='card_entry')
    attendance_reason   = fields.Text(string="Reasons")
    state               = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft')

    @api.multi            
    def attendance_confirm(self):
        for record in self:
            record.state = 'done'

    @api.multi
    def attendance_reset(self):
        for record in self:
            record.state = 'draft'
            
#     @api.model
#     def create(self, vals):
#         if vals.get('attendance_status') and vals.get('attendance_status') in ['present','partial','absent']:
#             vals['original_status'] = vals['attendance_status']
#         res = super(PappayaDailyAttendanceLine, self).create(vals)
#         return res

#     @api.multi
#     def write(self, vals):
#         if vals.get('attendance_status') and vals.get('attendance_status') in ['present','partial','absent']:
#             vals['original_status'] = vals['attendance_status']
#         res = super(PappayaDailyAttendanceLine, self).write(vals)
#         return res

class EmployeeAttendanceLine(models.Model):
    _inherit = 'hr.employee'

    working_days = fields.Integer('Working Days', compute='get_total_working_days')

    def get_total_working_days(self):
        for record in self:
            attendance = record.env['hr.daily.attendance.line'].search([('employee_id','=',record.id),('attendance_status','=','present'),('state','=','done')])
            if attendance:
                record.working_days = len(attendance)
            else:
                record.working_days = 0

