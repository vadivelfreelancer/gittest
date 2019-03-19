import odoo
from odoo import http
from odoo.http import request
from odoo.api import Environment
from odoo import SUPERUSER_ID
from odoo.addons.web.controllers.main import ensure_db
import datetime
import json
import logging
# from openpyxl.pivot import record
# from docutils.languages import fa
_logger = logging.getLogger(__name__)
from odoo.addons.web.controllers.main import Home
from odoo.tools.translate import _

class SingleSignOnController(http.Controller):

    def _login_redirect(self, uid, redirect=None):
        return redirect if redirect else '/web'

    @http.route('/ssosignin/auth/<string:userid>/<string:timestampstr>', type='http', auth="public", website=True)
    def mob_login(self, redirect=None,key='',timestampstr='', **kw):
        print (key,"================ need to uninstall auth encrypt module===========================",timestampstr)
        # return request.redirect('/web/login')
        ensure_db()
        request.params['status'] = False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)
        if not request.uid:
            request.uid = odoo.SUPERUSER_ID
        values = request.params.copy()


        # if request.httprequest.method == 'POST':
        old_uid = request.uid
        login = 'user001'#request.params['login']
        # password = '12345'#request.params['password']
        env = Environment(request.cr, SUPERUSER_ID, {})
        user_br = env['res.users'].search([('login', '=', login)])
        password = user_br.password
        print (password, "8888888888888888888888888888888888888665656565111111111111111")
        uid = request.session.authenticate(request.session.db, login, password)
        if uid is not False:
            request.params['login_success'] = True
            return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
        request.uid = old_uid
        values['error'] = _("Wrong login/password")

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
