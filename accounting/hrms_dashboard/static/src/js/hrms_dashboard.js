odoo.define('hrms_dashboard.Dashboard', function (require) {
"use strict";
var ajax = require('web.ajax');
var ControlPanelMixin = require('web.ControlPanelMixin');
var core = require('web.core');
var Dialog = require('web.Dialog');
var session = require('web.session');
var rpc = require('web.rpc');
var utils = require('web.utils');
var web_client = require('web.web_client');
var Widget = require('web.Widget');
var _t = core._t;
var QWeb = core.qweb;

var HrDashboard = Widget.extend(ControlPanelMixin, {
    template: "HrDashboardMain",
    events: {
        'click .hr_leave_allocations_approve': 'leave_allocations_to_approve',
        'click .hr_job_application_approve': 'job_applications_to_approve',
        'click .hr_payslip':'hr_payslip',
        'click .hr_job':'hr_job',
        'click .hr_employee':'hr_employee',
        'click .leaves_request_month':'leaves_request_month',
        'click .leaves_request_today':'leaves_request_today',
    },

    init: function(parent, context) {
        this._super(parent, context);
        this.login_employee = false;
        this.employee_birthday = [];
        this.upcoming_events = [];
        this.action_id = context.id;
        this._super(parent,context);
    },

    start: function() {
        var self = this;
        for(var i in self.breadcrumbs){
            self.breadcrumbs[i].title = "Dashboard";
        }
        self.update_control_panel({breadcrumbs: self.breadcrumbs}, {clear: true});
        rpc.query({
            model: "hr.employee",
            method: "get_user_employee_details",
        })
        .then(function (result) {
            if(result){
                self.login_employee =  result;
                var manager_view = $('.o_hr_dashboard').html(QWeb.render('ManagerDashboard', {widget: self}));
                self.render_graph();
                self.render_student_graph();
                $('.o_hr_dashboard').prepend(QWeb.render('LoginEmployeeDetails', {widget: self}));
                /*need to check user access levels*/
                session.user_has_group('hr.group_hr_manager').then(function(has_group){
                    if(has_group == false){
                        $('.employee_dashboard_main').css("display", "none");
                    }
                });

                /*Upcoming Birthdays, Events*/
                var today = new Date().toJSON().slice(0,10).replace(/-/g,'/');
                rpc.query({
                    model: "hr.employee",
                    method: "get_upcoming",
                })
                .then(function (res) {
                    self.employee_birthday = res['birthday'];
                        $('.o_hr_dashboard').append(QWeb.render('EmployeeDashboard', {widget: self}));
                    });
             }
            else{
                $('.o_hr_dashboard').html(QWeb.render('EmployeeWarning', {widget: self}));
                return;
            }
        });
    },


    on_reverse_breadcrumb: function() {
        this.update_control_panel({clear: true});
        web_client.do_push_state({action: this.action_id});
    },

    hr_payslip: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Employee Payslips"),
            type: 'ir.actions.act_window',
            res_model: 'hr.payslip',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['net_amount','>=', 0],['state','=', 'done']],
            target: 'current'
        }, options)
    },

    hr_job: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Designation"),
            type: 'ir.actions.act_window',
            res_model: 'hr.job',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['no_of_recruitment','>', 0]],
            target: 'current'
        }, options)
    },

    hr_employee: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Employee"),
            type: 'ir.actions.act_window',
            res_model: 'hr.employee',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['id','!=',1]],
            target: 'current'
        }, options)
    },

    leaves_request_month: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        var date = new Date();
        var firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
        var lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);
        var fday = firstDay.toJSON().slice(0,10).replace(/-/g,'-');
        var lday = lastDay.toJSON().slice(0,10).replace(/-/g,'-');
        this.do_action({
            name: _t("This Month Leaves"),
            type: 'ir.actions.act_window',
            res_model: 'hr.holidays',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['date_to','>', fday],['state','=','validate'],['date_from','<', lday], ['type','=','remove']],
            target: 'current'
        }, options)
    },

    leaves_request_today: function(e) {
        var self = this;
        var date = new Date();
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Leaves Today"),
            type: 'ir.actions.act_window',
            res_model: 'hr.holidays',
            view_mode: 'tree,form,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['type','=','remove'], ['date_from','<=', date], ['date_to', '>=', date], ['state','=','validate']],
            target: 'current'
        }, options)
    },

    job_applications_to_approve: function(event){
        var self = this;
        event.stopPropagation();
        event.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Applications"),
            type: 'ir.actions.act_window',
            res_model: 'hr.applicant',
            view_mode: 'tree,kanban,form,pivot,graph,calendar',
            view_type: 'form',
            views: [[false, 'list'],[false, 'kanban'],[false, 'form'],
                    [false, 'pivot'],[false, 'graph'],[false, 'calendar']],
            context: {},
            domain: [['short_list', '=', 'True']],
            target: 'current'
        }, options)
    },


    render_graph:function(){

        var self = this;
        var w = 200;
        var h = 200;
        var r = h/2;
        var elem = this.$('.emp_graph');
        var color = ['#ff8762', '#5ebade', '#b298e1', '#70cac1', '#cf2030'];

        rpc.query({
            model: "hr.employee",
            method: "get_dept_employee",
        }).then(function (data) {
        var margin = {top: 40, right: 20, bottom: 30, left: 40},
        width = 600 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;


        var formatPercent = d3.format(".0%");

        var x = d3.scale.ordinal()
        .rangeRoundBands([0, width], .1);

        var y = d3.scale.linear()
        .range([height, 0]);

        var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

        var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");
        //.tickFormat(formatPercent);

       var tooltip = d3.select("body").append("div").attr("class", "toolTip");


        var colors = ['#70cac1', '#659d4e', '#208cc2', '#4d6cb1', '#584999', '#8e559e', '#cf3650', '#f65337', '#fe7139','#ffa433', '#ffc25b', '#f8e54b'];
        var color = d3.scale.ordinal().range(colors);

        var svg = d3.select(elem[0]).append("svg:svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
         	.attr("fill", function(d, i) {
            return color[i]
         })
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
        x.domain(data.map(function(d) { return d.label; }));
        y.domain([0, d3.max(data, function(d) { return d.value; })]);

        svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

        svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("value");

        svg.selectAll(".bar")
        .append("g").attr("class", "bar")
        .data(data)
        .enter().append("rect")
        .attr("x", function(d) { return x(d.label); })
        .attr("width", x.rangeBand())
        .attr("y", function(d) { return y(d.value); })
        .attr("height", function(d) { return height - y(d.value); })
         .attr("fill", function(d, i) {
            return color(i)
        })
         .on("mousemove", function(d){
            tooltip
              .style("left", d3.event.pageX - 50 + "px")
              .style("top", d3.event.pageY - 70 + "px")
              .style("display", "inline-block")
              .html((d.label) + "<br>"  + (d.value));
        })
    		.on("mouseout", function(d){ tooltip.style("display", "none");});


         //legend code
            let label = data.map(a => a.label);
            let dept_value = data.map(a => a.value)


            var legend = d3.select(elem[0]).append("table").attr('class','legend');

            // create one row per segment.
            var tr = legend.append("tbody").selectAll("tr").data(data).enter().append("tr");

            // create the first column for each segment.
            tr.append("td").append("svg").attr("width", '16').attr("height", '16').append("rect")
                .attr("width", '16').attr("height", '16')
                .attr("fill",function(d, i){ return color(i) });

            // create the second column for each segment.
            tr.append("td").text(function (d, i) {
                    return label[i];
                });

            // create the third column for each segment.
            tr.append("td").attr("class",'legendFreq')
               .text(function (d, i) {
                    return dept_value[i];
             });

        function type(d) {
        d.value = +d.value;
        return d;
        }

        });
        },

    render_student_graph:function(){
        var self = this;
        var w = 200;
        var h = 200;
        var r = h/2;
        var elem = this.$('.student_graph');
        var  margin = {left: 200 , bottom : 85 }
         var tooltip = d3.select("body").append("div").attr("class", "toolTip");
        var colors = ['#70cac1', '#659d4e', '#208cc2', '#4d6cb1', '#584999', '#8e559e', '#cf3650', '#f65337', '#fe7139',
        '#ffa433', '#ffc25b', '#f8e54b'];
        var color = d3.scale.ordinal().range(colors);
        rpc.query({
            model: "hr.employee",
            method: "get_branch_student",
        }).then(function (data) {
            var segColor = {};
            var vis = d3.select(elem[0]).append("svg:svg").data([data]).attr("width", w).style("margin-left" , "200")
            .attr("height", h + margin.bottom).append("svg:g").attr("transform", "translate(" + r + "," + r + ")");
            var pie = d3.layout.pie().value(function(d){return d.value;});
            var arc = d3.svg.arc().outerRadius(r);
            var arcs = vis.selectAll("g.slice").data(pie).enter().append("svg:g").attr("class", "slice");
            arcs.append("svg:path")
                .attr("fill", function(d, i){
                    return color(i);
                })
                .attr("d", function (d) {
                    return arc(d);
                })
              .on("mousemove", function(d){
            tooltip
              .style("left", d3.event.pageX - 50 + "px")
              .style("top", d3.event.pageY - 70 + "px")
              .style("display", "inline-block")
              .html((d.data.label) + "<br>"  + (d.data.value));
                })
    		.on("mouseout", function(d){ tooltip.style("display", "none");});



            var legend = d3.select(elem[0]).append("table").attr('class','legend');

            // create one row per segment.
            var tr = legend.append("tbody").selectAll("tr").data(data).enter().append("tr");

            // create the first column for each segment.
            tr.append("td").append("svg").attr("width", '16').attr("height", '16').append("rect")
                .attr("width", '16').attr("height", '16')
                .attr("fill",function(d, i){ return color(i) });

            // create the second column for each segment.
            tr.append("td").text(function(d){ return d.label;});

            // create the third column for each segment.
            tr.append("td").attr("class",'legendFreq')
                .text(function(d){ return d.value;});



        });

    },

});

core.action_registry.add('hr_dashboard', HrDashboard);

return HrDashboard;

});
