odoo.define('pappaya_marketing.address_collection', function (require) {

    "use strict";
    var core = require("web.core");
    var Widget = require("web.Widget");
    var rpc = require('web.rpc');

    var o2m_report;
    
    var address_collection = Widget.extend({
        template: "ReportAddressCollection",
        events: {
            'click #saveUser' : 'formSubmit',
            'click #btn-hide-fields': 'hideFields',
            'click #loadData': 'btn_clk_load_data',
            'change select[name="report_type"]': 'fields_view_on_report_type'
        },

        start: function() {
        	var self = this;
        	var sup = self._super.apply(self, arguments);
            self.search_handlers();
            self.load_masters();
            self.$("select[name='state_ids']").on("keydown", function(e) {
                console.log("Keydown event");
            });
            self.init_fields();
            return sup;
        },

        init_dt: function() {
            var self = this;
            o2m_report = self.$('#o2m_report').DataTable({
            	'lengthMenu': [10, 50, 100, 200, 500, 1000],
            	'pageLength': 50,
            	'buttons': ['excel', 'pdf']
            });
        },

        init_fields: function() {
            var self = this;
            $(self.$("select[name='payroll_branch_ids']")[0].parentNode).hide();
            $(self.$("select[name='employee_ids']")[0].parentNode).hide();
            $(self.$("select[name='state_ids']")[0].parentNode).show();
            $(self.$("select[name='district_ids']")[0].parentNode).show();
            $(self.$("select[name='branch_ids']")[0].parentNode).show();
        },

        fields_view_on_report_type: function() {
            var self = this;
            var report_type = self.$("select[name='report_type']").val();

            if (report_type == 'branch') {
                $(self.$("select[name='payroll_branch_ids']")[0].parentNode).hide();
                $(self.$("select[name='employee_ids']")[0].parentNode).hide();
                $(self.$("select[name='state_ids']")[0].parentNode).show();
                $(self.$("select[name='district_ids']")[0].parentNode).show();
                $(self.$("select[name='branch_ids']")[0].parentNode).show();
            }
            else if (report_type == 'branch_and_employee') {
                $(self.$("select[name='payroll_branch_ids']")[0].parentNode).show();
                $(self.$("select[name='employee_ids']")[0].parentNode).show();
                $(self.$("select[name='state_ids']")[0].parentNode).show();
                $(self.$("select[name='district_ids']")[0].parentNode).show();
                $(self.$("select[name='branch_ids']")[0].parentNode).show();
            }
            else {
                $(self.$("select[name='payroll_branch_ids']")[0].parentNode).show();
                $(self.$("select[name='employee_ids']")[0].parentNode).show();
                $(self.$("select[name='state_ids']")[0].parentNode).hide();
                $(self.$("select[name='district_ids']")[0].parentNode).hide();
                $(self.$("select[name='branch_ids']")[0].parentNode).hide();
            } 
        },

        search_handlers: function() {
            var self = this;

            var domain = self.$("select[name='district_ids']").on("keyup", function() {
                var domain = [['name', 'ilike', 'tam']];
                self.load_district(domain);
            });

        },

        btn_clk_load_data: function() {
            var self = this;

            var report_type = $("select[name='report_type'").val();
            var state_ids = $("select[name='state_ids']").val();
            var district_ids = $("select[name='district_ids']").val();
            var branch_ids = $("select[name='branch_ids']").val();
            var payroll_branch_ids = $("select[name='payroll_branch_ids']").val();
            var employee_ids = $("select[name='employee_ids']").val();
            var lead_course_ids = $("select[name='lead_course_ids']").val();
            var is_class_wise = $("input[name='is_class_wise']").is(":checked");

            rpc.query({
                model: 'pappaya.lead.stud.address',
                method: 'address_collection_report',
                args: [report_type, state_ids, district_ids, branch_ids, payroll_branch_ids, employee_ids, lead_course_ids, is_class_wise]
            }).then(function (res) {
                    var heads = res['headers'];
                    var ths = "<thead><tr>";
                    $.each(heads, function(idx, head) {
                        ths += "<th>" + head + "</th>";
                    });
                    ths += "</tr></thead>";

                    var trs = "";
                    $.each(res['result'], function(idx, obj) {
                        trs += "<tr>";
                        $.each(heads, function(i, k) {
                            var value = obj[k] == undefined ? 0 : obj[k];
                            console.log("Value => ", value);
                            trs += "<td>" + value + "</td>";
                        });
                        trs += "</tr>";
                    });

                    var table = ths + trs;
                    if (o2m_report !== undefined) {
                        o2m_report.destroy();
                    }
                    self.$("#o2m_report").empty()
                    .append(table);
                    self.init_dt();
            });
        },


        load_masters: function() {
            var self = this;
            self.load_state();
            self.load_district();
            self.load_branch();
            self.load_payroll_branch();
            self.load_employee();
            self.load_course();
        },

        load_state: function(domain=[]) {
            var self = this;
            self._rpc({
                model: 'res.country.state',
                method: 'search_read',
                domain: domain,
                fields: ['id', 'name'],
                limit: 10
            }).then(function(datas) {
                if (datas) {
                    var states = self.$("select[name='state_ids']");

                    var options = "";
                    $.each(Object.keys(datas), function(idx, key) {
                        options += `<option value="${datas[key].id}">${datas[key].name}</option>\n`
                    });

                    states.empty()
                    .append(options)
                    .select2();
                }
            });
        },

        load_district: function(domain=[]) {
            var self = this;
            self._rpc({
                model: 'state.district',
                method: 'search_read',
                domain: domain,
                fields: ['id', 'name'],
                limit: 10
            }).then(function(datas) {
                if (datas) {
                    var districts = self.$("select[name='district_ids']");

                    var options = "";
                    $.each(Object.keys(datas), function(idx, key) {
                        options += `<option value="${key}">${datas[key].name}</option>\n`
                    });
                    districts.empty()
                    .append(options)
                    .select2();
                }
            });
        },

        load_branch: function(domain=[]) {
            var self = this;
            self._rpc({
                model: 'res.company',
                method: 'search_read',
                domain: domain,
                fields: ['id', 'name'],
                limit: 10
            }).then(function(datas) {
                if (datas) {
                    var branches = self.$("select[name='branch_ids']");

                    var options = "";
                    $.each(Object.keys(datas), function(idx, key) {
                        options += `<option value="${key}">${datas[key].name}</option>\n`
                    });
                    branches.append(options)
                    .select2();
                }
            });
        },

        load_payroll_branch: function(domain=[]) {
            var self = this;
            self._rpc({
                model: 'pappaya.payroll.branch',
                method: 'search_read',
                domain: domain,
                fields: ['id', 'name'],
                limit: 10
            }).then(function(datas) {
                if (datas) {
                    var payroll_branches = self.$("select[name='payroll_branch_ids']");

                    var options = "";
                    $.each(Object.keys(datas), function(idx, key) {
                        options += `<option value="${key}">${datas[key].name}</option>\n`
                    });
                    payroll_branches.append(options)
                    .select2();
                }
            });
        },

        load_employee: function(domain=[]) {
            var self = this;
            self._rpc({
                model: 'hr.employee',
                method: 'search_read',
                domain: domain,
                fields: ['id', 'name'],
                limit: 10
            }).then(function(datas) {
                if (datas) {
                    var employees = self.$("select[name='employee_ids']");

                    var options = "";
                    $.each(Object.keys(datas), function(idx, key) {
                        options += `<option value="${key}">${datas[key].name}</option>\n`
                    });
                    employees.append(options)
                    .select2();
                }
            });
        },

        load_course: function(domain=[]) {
            var self = this;
            self._rpc({
                model: 'pappaya.lead.course',
                method: 'search_read',
                domain: domain,
                fields: ['id', 'name'],
                limit: 10
            }).then(function(datas) {
                if (datas) {
                    var courses = self.$("select[name='course_ids']");

                    var options = "";
                    $.each(Object.keys(datas), function(idx, key) {
                        options += `<option value="${key}">${datas[key].name}</option>\n`
                    });
                    courses.append(options)
                    .select2();
                }
            });
        } 
        
    });
    
    core.action_registry.add("pappaya_marketing.address_collection", address_collection);    
    return address_collection;
});