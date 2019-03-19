# -*- coding: utf-8 -*-
import logging
import random
import select
import threading
import time
from datetime import datetime
from pytz import timezone
import odoo
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
# import xmlrpclib
import socket  # for sockets
import sys  # for exit

_logger = logging.getLogger(__name__)
TIMEOUT = 50

from odoo import fields, models, api, _

# ----------------------------------------------------------
class rfidSocket(object):
    def call_method(self, v):
        config = odoo.tools.config
        dbname = config['db_name']
        registry = odoo.registry(dbname)

        fmt_date = "%Y-%m-%d"
        fmt_hour = "%H"

        # Current time in UTC
        now_utc = datetime.now(timezone('UTC'))

        today_date = datetime.now().strftime(fmt_date)
        today_hour = int(datetime.now().strftime(fmt_hour))

        with odoo.api.Environment.manage():
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                
                orm_user = env['res.users']
                orm_student = env['res.partner']
                # orm_attend_line = env['pappaya.attendance.line']
                orm_rfid_data = env['pappaya.rfid.tracking.data']                
                print (registry.cursor(), "registry.cursor()registry.cursor()")
                user_tz = orm_user.search([('id','=',1)]).tz
                now_asia = now_utc.astimezone(timezone(user_tz))
                utc_hour = now_asia.strftime(fmt_hour)
                print (v, type(v), "VALUe")
                
                stud_ids = orm_student.search([('rfid_card_no', '=', v.strip())])
                if len(stud_ids) < 1:
                    orm_rfid_data.create({'rfid_card_id': v,
                                          'capture_datetime': datetime.now()
                                        })
                print (v, "VVVVVVVVVVVVVVVVVVVV", stud_ids)
                
#                 for student_id in stud_ids:
#                     _logger.info("=====>>   " + student_id.name + "   <<====")
#                     
#                     # student_id = orm_student.browse(cr, odoo.SUPERUSER_ID, s)
#                     
#                     attend_line_ids = orm_attend_line.search([('student_id', '=', student_id.id), (
#                     'attendance_date', '=', today_date)])
#                     # ~ print attend_line_ids,"=====",utc_hour
#                     if not attend_line_ids:
#                         if utc_hour < 13:
#                             orm_attend_line.create({'student_id': student_id.id,
#                                                                               'attendance_date': today_date,
#                                                                               # 'grade_id': student_id.grade_id.id,
#                                                                               # 'section_id': student_id.section_id.id,
#                                                                               'school_id': student_id.school_id.id,
#                                                                               'present_morning': True,
#                                                                               })
#                         else:
#                             orm_attend_line.create({'student_id': student_id.id,
#                                                                               'attendance_date': today_date,
#                                                                               # 'grade_id': student_id.grade_id.id,
#                                                                               # 'section_id': student_id.section_id.id,
#                                                                               'school_id': student_id.school_id.id,
#                                                                               'present_afternoon': True,
#                                                                               })
#                     else:
#                         if utc_hour < 13:
#                             orm_attend_line.write(attend_line_ids[0], {
#                                 'present_morning': True,
#                             })
#                         else:
#                             orm_attend_line.write(attend_line_ids[0], {
#                                 'present_afternoon': True,
#                             })
# 
#                     # ==================== Every Data as Captured in Separate Table ============
#                     orm_rfid_data.create({'student_id': student_id.id,
#                                                                         'rfid_card_id': v,
#                                                                         'capture_datetime': datetime.now(),
#                                                                         # 'grade_id': student_id.grade_id.id,
#                                                                         # 'section_id': student_id.section_id.id,
#                                                                         'school_id': student_id.school_id.id,
# 
#                                                                         })
# 
#                 orm_rfid_data.create({
#                                                                     'rfid_card_id': v,
#                                                                     'capture_datetime': datetime.now(),
# 
#                                                                     })

        return True

    def get_rfid_device_url(self):
        config = odoo.tools.config
        dbname = config['db_name']
        registry = odoo.registry(dbname)
        orm_sys_param = registry.get('ir.config_parameter')
        with odoo.api.Environment.manage():
            with registry.cursor() as cr:
                rfid_url = orm_sys_param.get_param(cr, odoo.SUPERUSER_ID, 'RFID_DEVICE_URL')
                return rfid_url

    def loop(self, url_port):
        _logger.info("Bus RFID.loop listen imbus on db postgres")

        # create an INET, STREAMing socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            _logger.info("Failed to create socket")
            sys.exit()
        _logger.info('======================== Socket Created == ' + url_port)

        # url_port=self.get_rfid_device_url()
        host = url_port.split(':')[0]
        port = int(url_port.split(':')[1])
        # Connect to remote server
        try:
            s.connect((host, port))
            _logger.info('!!!!!!!!!!!!!!  !!!!!!!!!!!! Socket Connected to ' + host + ' on ' + str(port))
        except Exception as e:
            _logger.info("========= Exception as == == == xx xx xx xx "+ str(e) + "=="+str(e.args))
            return True


        while True:
            print ("Checking to read..")
            command = b'1'
            s.send(command)
            reply = s.recv(1024)
            print (reply, "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            _logger.info("       =======>> " + str(reply))
            if reply:
                self.call_method(str(reply)[1:])

    # def run(self):
    #     while True:
    #         try:
    #             self.loop()
    #         except Exception, e:
    #             _logger.exception("Bus RFID.loop error, sleep and retry")
    #             time.sleep(TIMEOUT)

    def start(self):
        param = ''
        try:
            # create an empty registry
            config = odoo.tools.config
            dbname = config['db_name']
            registry = odoo.modules.registry.Registry(dbname)
            with registry.cursor() as cr:
                # cr.execute(""" select  value from ir_config_parameter where key='RFID_DEVICE_URL' """, )
                cr.execute(""" select rfid_device_ip from res_company where type='branch' """, )
                param = cr.fetchall()

        except Exception as e:
            _logger.exception("Configuratiobdan not done properly")
        
#         print (param, "paramparam program started")
        if odoo.evented:
            # gevent mode
            import gevent
            self.Event = gevent.event.Event
            gevent.spawn(self.run)
        elif odoo.multi_process:
            # disabled in prefork mode
            return
        else:
            # threaded mode
            if param:
                for par in param:
                    if par[0] != None:
                        for p in par[0].split(','):

                            self.Event = threading.Event
                            t = threading.Thread(name="%s.Bus" % __name__, target=self.loop, args=(p,))
                            t.daemon = True
                            t.start()
        return self


rf_soc = rfidSocket().start()
