from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta as td
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

days_details = ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31']

class PappayaAttendanceReport(models.TransientModel):
    _name = 'pappaya.attendance.report'
    
    branch_id = fields.Many2one('operating.unit', 'Branch', domain=[('type','=','branch')])
    month_id = fields.Many2one('calendar.generation.line',string='Month')
    date_start = fields.Date(string='Date From')
    date_end = fields.Date(string='Date To')
    total_days = fields.Integer(compute='_get_total_days', string="Total Days")
    
    @api.onchange('month_id')
    def onchange_month_id(self):
        for record in self:
            if record.month_id:
                record.date_start = record.month_id.date_start
                record.date_end   = record.month_id.date_end
                
    def _get_total_days(self):
        for record in self:
            delta = datetime.strptime(record.date_end, '%Y-%m-%d') - datetime.strptime(record.date_start, '%Y-%m-%d')
            record.total_days = delta.days+1
                
    @api.multi
    def generate_pdf_report(self):
        return self.env.ref('pappaya_hr_attendance.pdf_view_pappaya_attendance_report').get_report_action(self)
    
    @api.multi
    def get_data(self):
        data_list = []
        for record in self:
            month = datetime.strptime(record.date_start,'%Y-%m-%d').month
            year = datetime.strptime(record.date_start,'%Y-%m-%d').year
            if month < 9:
                month = '0'+str(month)
            month_year = month+'-'+str(year)
            
            self._cr.execute("""
                CREATE OR REPLACE FUNCTION CALCULATE_EMPLOYEE_DAYS (employeeId INTEGER, startDate DATE, endDate DATE, branchId INTEGER)
                    RETURNS RECORD
                    AS $$
                DECLARE
                hrCalendarId INTEGER;
                    lastPresentDate DATE;
                    lastLeave DATE;
                    
                   -- hrCalendarId INTEGER;
                    numberWeeklyOff FLOAT;
                    numberHoliday FLOAT;
                    reversableLeaveDays FLOAT;
                    numberDaysPresent INTEGER;
                    numberDaysPartialPresent INTEGER;
                    --numberHoursPresent FLOAT;
                    --numberHoursPartialPresent FLOAT;
                    numberLeaves FLOAT;
                    workedDaysCounter INTEGER;
                    returnRecord RECORD;
                BEGIN
                
                    select HR_HCL.date INTO lastLeave
                    FROM
                                            hr_holidays hr_ho,
                                            hr_holidays_calendar_line HR_HCL
                                        WHERE ((hr_ho.date_from >= startDate
                                                AND hr_ho.date_from <= endDate)
                                            OR (hr_ho.date_to >= startDate
                                                AND hr_ho.date_to <= endDate))
                                        AND employee_id = employeeId
                                        AND TYPE = 'remove'
                                        AND HR_HCL.holidays_id = HR_HO.id
                                        AND HR_HCL.DATE >= startDate
                                        AND HR_HCL.DATE <= endDate
                                        AND HR_HO.state = 'validate'
                    order by HR_HCL.date desc limit 1;                
                
                
                    SELECT
                        attendance_date INTO lastPresentDate
                    FROM
                        hr_daily_attendance_line
                    WHERE
                        attendance_date >= startDate
                        AND attendance_date <= endDate
                        AND attendance_status IN ('present', 'partial')
                        AND employee_id = employeeId
                        AND state = 'done'
                    ORDER BY
                        attendance_date DESC
                    LIMIT 1;
                    
                    IF lastPresentDate IS NOT NULL  AND lastLeave IS NOT NULL THEN
                            lastPresentDate = GREATEST(lastPresentDate::date,lastLeave::date); 
                     ELSIF lastPresentDate IS NULL THEN 
                                               lastPresentDate = lastLeave;
                    END IF;                    
                    
                    
                    
                    
                    raise notice 'start Date %   %', startDate, lastPresentDate;
                 IF lastPresentDate IS NOT NULL THEN
                        SELECT
                            id INTO hrCalendarId
                        FROM
                            hr_calendar
                        WHERE
                            branch_id = branchId
                            AND date_from = startDate
                            AND date_to = endDate
                        ORDER BY
                            startDate DESC
                        LIMIT 1;
                         SELECT
                            COUNT(1) INTO numberWeeklyOff
                        FROM
                            hr_calendar_line hrc
                        WHERE
                            calendar_id = hrCalendarId
                            AND HRC.DATE >= startDate
                            AND HRC.DATE <= lastPresentDate
                            AND work_type = 'week_off'
                            and HRC.DATE not in (sELECT HR_HCL.DATE
                                    FROM
                                        hr_holidays hr_ho,
                                        hr_holidays_calendar_line HR_HCL
                                    WHERE ((hr_ho.date_from >= startDate
                                            AND hr_ho.date_from <= endDate)
                                        OR (hr_ho.date_to >= startDate
                                            AND hr_ho.date_to <= endDate))
                                    AND employee_id = employeeId
                                    AND TYPE = 'remove'
                                    AND HR_HCL.holidays_id = HR_HO.id
                                    AND HR_HCL.DATE >= startDate
                                    AND HR_HCL.DATE <= endDate
                                    AND HR_HO.state = 'validate');

                        SELECT
                            COUNT(1) INTO numberHoliday
                        FROM
                            hr_calendar_line hrc
                        WHERE
                            calendar_id = hrCalendarId
                            AND HRC.DATE >= startDate
                            AND HRC.DATE <= lastPresentDate
                            AND work_type = 'holiday'and HRC.DATE not in (sELECT HR_HCL.DATE
                                    FROM
                                        hr_holidays hr_ho,
                                        hr_holidays_calendar_line HR_HCL
                                    WHERE ((hr_ho.date_from >= startDate
                                            AND hr_ho.date_from <= endDate)
                                        OR (hr_ho.date_to >= startDate
                                            AND hr_ho.date_to <= endDate))
                                    AND employee_id = employeeId
                                    AND TYPE = 'remove'
                                    AND HR_HCL.holidays_id = HR_HO.id
                                    AND HR_HCL.DATE >= startDate
                                    AND HR_HCL.DATE <= endDate
                                    AND HR_HO.state = 'validate');

                        SELECT
                            COALESCE(COUNT(*), 0) INTO numberDaysPresent
                        FROM
                            hr_daily_attendance_line
                        WHERE
                            employee_id = employeeId
                            AND attendance_date >= startDate
                            AND attendance_date <= lastPresentDate
                            AND attendance_status = 'present'
                            AND state = 'done'
                            AND attendance_date IN (
                                SELECT
                                    HRC.DATE
                                FROM
                                    hr_calendar_line hrc
                                WHERE
                                    calendar_id = hrCalendarId
                                    AND HRC.DATE >= startDate
                                    AND HRC.DATE <= lastPresentDate
                                    AND work_type = 'work');
                        SELECT
                            COALESCE(COUNT(*), 0) INTO numberDaysPartialPresent
                        FROM
                            hr_daily_attendance_line
                        WHERE
                            employee_id = employeeId
                            AND attendance_date >= startDate
                            AND attendance_date <= lastPresentDate
                            AND attendance_status = 'partial'
                            AND state = 'done'
                            AND attendance_date IN (
                                SELECT
                                    HRC.DATE
                                FROM
                                    hr_calendar_line hrc
                                WHERE
                                    calendar_id = hrCalendarId
                                    AND HRC.DATE >= startDate
                                    AND HRC.DATE <= lastPresentDate
                                    AND work_type = 'work');
                        RAISE NOTICE 'numberDaysPresent %', numberDaysPresent;
                        reversableLeaveDays = 0;
                        SELECT
                            COALESCE(SUM(
                                    CASE WHEN (HR_HCL.parts_of_the_day = 'full_day'  or HR_HCL.parts_of_the_day = 'half_full_day')
                                        AND attendance_status = 'present' THEN
                                        1
                                    WHEN HR_HCL.parts_of_the_day = 'half_day'
                                        AND attendance_status = 'present' THEN
                                        0.5
                                    WHEN (HR_HCL.parts_of_the_day = 'full_day'  or HR_HCL.parts_of_the_day = 'half_full_day')
                                        AND attendance_status = 'partial' THEN
                                        0.5
                                    END), 0) INTO reversableLeaveDays
                        FROM
                            hr_holidays hr_ho,
                            hr_holidays_calendar_line HR_HCL,
                            hr_daily_attendance_line hr_at_ln
                        WHERE ((hr_ho.date_from >= startDate
                                AND hr_ho.date_from <= endDate)
                            OR (hr_ho.date_to >= startDate
                                AND hr_ho.date_to <= endDate))
                        AND hr_ho.employee_id = employeeId
                        AND TYPE = 'remove'
                        AND HR_HCL.holidays_id = HR_HO.id
                        AND HR_HCL.DATE >= startDate
                        AND HR_HCL.DATE <= endDate
                        AND HR_HO.state = 'validate'
                        AND hr_at_ln.employee_id = employeeId
                        AND hr_at_ln.state = 'done'
                        AND HR_HCL.DATE = attendance_date
                        AND attendance_date IN (
                                SELECT
                                    HRC.DATE
                                FROM
                                    hr_calendar_line hrc
                                WHERE
                                    calendar_id = hrCalendarId
                                    AND HRC.DATE >= startDate
                                    AND HRC.DATE <= lastPresentDate
                                    AND work_type = 'work');
                                    SELECT
                                        COALESCE(SUM(
                                                CASE WHEN HR_HCL.parts_of_the_day = 'half_day' THEN
                                                    (0.5)
                                                ELSE
                                                    1
                                                END), 0) INTO numberLeaves
                                    FROM
                                        hr_holidays hr_ho,
                                        hr_holidays_calendar_line HR_HCL
                                    WHERE ((hr_ho.date_from >= startDate
                                            AND hr_ho.date_from <= endDate)
                                        OR (hr_ho.date_to >= startDate
                                            AND hr_ho.date_to <= endDate))
                                    AND employee_id = employeeId
                                    AND TYPE = 'remove'
                                    AND HR_HCL.holidays_id = HR_HO.id
                                    AND HR_HCL.DATE >= startDate
                                    AND HR_HCL.DATE <= endDate
                                    AND HR_HO.state = 'validate';
                raise notice 'reversableLeaveDays %',reversableLeaveDays;
                raise notice '(numberDaysPresent + (numberDaysPartialPresent * 0.5) - reversableLeaveDays ) %',(numberDaysPresent + (numberDaysPartialPresent * 0.5) - reversableLeaveDays );
                
                select (numberDaysPresent + (numberDaysPartialPresent * 0.5) - reversableLeaveDays )::float  numbberOfDaysPresent, numberLeaves::float  , numberWeeklyOff::float , numberHoliday::float  into returnRecord;
                
                ELSE
                select 0::float as numbberOfDaysPresent, 0::float  as numberLeaves , 0::float  as numberWeeklyOff, 0::float  as numberHoliday into returnRecord;
                
                
                
                END IF;
                   
                RETURN returnRecord;
                
                END;
                $$
                LANGUAGE PLPGSQL;            
            """)            
            self._cr.execute("""
                 CREATE EXTENSION IF NOT EXISTS tablefunc;
                select b.*,x.* from (
                select ROW_NUMBER () over (order by emp.emp_id) as s_no, emp.emp_id, emp.id, emp.name , a.* from (
                SELECT
                    *
                FROM
                    CROSSTAB ($$
                        SELECT
                            tempA.employee_id,
                            at_date,
                            CASE WHEN COALESCE(parts_of_the_day, COALESCE(status, 'absent')) = 'present' THEN 'PR' 
                                 WHEN COALESCE(parts_of_the_day, COALESCE(status, 'absent')) = 'absent' THEN 'AB'  
                                 WHEN COALESCE(parts_of_the_day, COALESCE(status, 'absent')) = 'half_day' THEN 'HL'  
                                 WHEN COALESCE(parts_of_the_day, COALESCE(status, 'absent')) = 'Leave' THEN 'L'
                                 WHEN COALESCE(parts_of_the_day, COALESCE(status, 'absent')) = 'partial' THEN 'PP'
                                 WHEN COALESCE(parts_of_the_day, COALESCE(status, 'absent')) = 'week_off' THEN 'WO'
                                 WHEN COALESCE(parts_of_the_day, COALESCE(status, 'absent')) = 'holiday' THEN 'HD'
                                 ELSE COALESCE(parts_of_the_day, COALESCE(status, 'absent'))  
                END
                        FROM (
                            SELECT
                                hral.employee_ID,
                                to_char(hral.attendance_date, 'DD')::bigint at_date,
                                hral.attendance_date,
                                CASE WHEN hrcl.work_type != 'work' THEN
                                    hrcl.work_type
                                ELSE
                                    hral.attendance_status
                                END AS status
                            FROM
                                hr_daily_attendance hra,
                                hr_calendar hrc,
                                hr_calendar_line hrcl,
                                hr_daily_attendance_line hral
                            WHERE
                                hra.id = hral.daily_attendance_id
                                AND to_char(hra.attendance_date, 'MM-YYYY') = %s
                                AND hra.branch_id = %s
                                AND hrc.branch_id = hra.branch_id                
                                AND hrcl.calendar_id = hrc.id
                                AND hral.state = 'done'
                                --and hral.employee_id = 270880
                                AND hra.attendance_date = hrcl.date
                                 ) tempA
                        LEFT OUTER JOIN (
                        SELECT
                            employee_id, CASE WHEN parts_of_the_day = 'Half Leave' THEN
                                'Half Leave'
                            ELSE
                                'Leave'
                            END AS parts_of_the_day, date, date_from, date_to
                        FROM
                            hr_holidays hrh,
                            hr_holidays_calendar_line hrhcl
                        WHERE
                            hrh.id = hrhcl.holidays_id and hrh.state = 'validate'
                            AND TYPE = 'remove') tempB ON tempA.employee_id = tempB.employee_id
                        AND tempA.attendance_date = tempB.date
                    ORDER BY
                        1,
                        2 $$,
                        $$
                        SELECT
                            generate_series(1, 31) -- should be (1, 31)
                            $$) AS final_result (employee_id INTEGER,
                        "1" character varying,
                        "2" character varying,
                        "3" character varying,
                        "4" character varying,
                        "5" character varying,
                        "6" character varying,
                        "7" character varying,
                        "8" character varying,
                        "9" character varying,
                        "10" character varying,
                        "11" character varying,
                        "12" character varying,
                        "13" character varying,
                        "14" character varying,
                        "15" character varying,
                        "16" character varying,
                        "17" character varying,
                        "18" character varying,
                        "19" character varying,
                        "20" character varying,
                        "21" character varying,
                        "22" character varying,
                        "23" character varying,
                        "24" character varying,
                        "25" character varying,
                        "26" character varying,
                        "27" character varying,
                        "28" character varying,
                        "29" character varying,
                        "30" character varying,
                        "31" character varying)
                
                ) A, hr_employee emp 
                
                where a.employee_id = emp.id) b
                JOIN LATERAL (select * from CALCULATE_EMPLOYEE_DAYS(b.id,%s,%s,%s) t(present_days float, leave_days float, weekly_off float, holiday float ) ) x on true ;
                
                ;
            """, (month_year, record.branch_id.id, record.date_start, record.date_end,record.branch_id.id))
            
            for data in self._cr.dictfetchall():
                for column in data.keys():
                    if column in days_details and not data[column]:
                        data[column] = 'AB'

                present_days = data['present_days']
                leave_days = data['leave_days']
                weekly_off = data['weekly_off']
                holiday = data['holiday']
                total_days = (present_days + leave_days + weekly_off + holiday)

                data.update({
                    'present_days': present_days,
                    'leave_days' : leave_days,
                    'weekly_off': weekly_off,
                    'holiday':holiday,
                    'absent': (record.total_days - total_days)
                    })
                data_list.append(data)
            return data_list

    