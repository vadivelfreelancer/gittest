odoo.define('pappaya_debranding11.title', function(require) {
"use strict";

var core = require('web.core');
var utils = require('web.utils');
var ajax = require('web.ajax');
var Dialog = require('web.Dialog');
var WebClient = require('web.AbstractWebClient');
var CrashManager = require('web.CrashManager'); // We can import crash_manager also
var concurrency = require('web.concurrency');
var mixins = require('web.mixins');
var session = require('web.session');
var crash_manager = require('web.crash_manager');
var SearchView = require('web.SearchView');
var FavoriteMenu = require('web.FavoriteMenu');
var FilterMenu = require('web.FilterMenu');
var GroupByMenu = require('web.GroupByMenu');

var QWeb = core.qweb;
var _t = core._t;
var _lt = core._lt;


var map_title ={
    user_error: _lt('Warning'),
    warning: _lt('Warning'),
    access_error: _lt('Access Warning'),
    missing_error: _lt('Missing Record'),
    validation_error: _lt('Validation Warning'),
    except_orm: _lt('Global Business Warning'),
    access_denied: _lt('Access Denied'),
};

//WebClient.include({
//init: function (parent) {
//    this.client_options = {};
//    mixins.ServiceProvider.init.call(this);
//    this._super(parent);
//    this.origin = undefined;
//    this._current_state = null;
//    this.menu_dm = new concurrency.DropMisordered();
//    this.action_mutex = new concurrency.Mutex();
//    var self = this;
//    // Rpc call to fetch the company name from model
//    this._rpc({
//        fields: ['company_name',],
//        domain: [],
//        model: 'website',
//        method: 'search_read',
//        limit: 1,
//        context: session.user_context,
//    }).done(function(result){
//        self.set('title_part', {"zopenerp": 'Pappaya'});
//    });
//    },
//});
CrashManager.include({
    rpc_error: function(error) {
        var self = this;
        if (!this.active) {
            return;
        }
        if (this.connection_lost) {
            return;
        }
        if (error.code === -32098) {
            core.bus.trigger('connection_lost');
            this.connection_lost = true;
            var timeinterval = setInterval(function() {
                ajax.jsonRpc('/web/webclient/version_info').then(function() {
                    clearInterval(timeinterval);
                    core.bus.trigger('connection_restored');
                    self.connection_lost = false;
                });
            }, 2000);
            return;
        }
        var handler = core.crash_registry.get(error.data.name, true);
        if (handler) {
            new (handler)(this, error).display();
            return;
        }
        if (error.data.name === "odoo.http.SessionExpiredException" || error.data.name === "werkzeug.exceptions.Forbidden") {
            this.show_warning({type: _t("Session Expired"), data: {message: _t("Your session expired. Please refresh the current web page.")}});
            return;
        }
        if (_.has(map_title, error.data.exception_type)) {
            if(error.data.exception_type === 'except_orm'){
                if(error.data.arguments[1]) {
                    error = _.extend({}, error,
                                {
                                    data: _.extend({}, error.data,
                                        {
                                            message: error.data.arguments[1],
                                            title: error.data.arguments[0] !== 'Warning' ? (" - " + error.data.arguments[0]) : '',
                                        })
                                });
                }
                else {
                    error = _.extend({}, error,
                                {
                                    data: _.extend({}, error.data,
                                        {
                                            message: error.data.arguments[0],
                                            title:  '',
                                        })
                                });
                }
            }
            else {
                error = _.extend({}, error,
                            {
                                data: _.extend({}, error.data,
                                    {
                                        message: error.data.arguments[0],
                                        title: map_title[error.data.exception_type] !== 'Warning' ? (" - " + map_title[error.data.exception_type]) : '',
                                    })
                            });
            }

            this.show_warning(error);
        //InternalError

        } else {
            this.show_error(error);
        }
    },
    show_warning: function(error) {
        if (!this.active) {
            return;
        }
        // Error message contains odoo title. Replace it
        error.message = "Alert"
        
        // error.message = error.message && error.message.replace("Odoo", "")
        new Dialog(this, {
            size: 'medium',
            title: _.str.capitalize(error.type || error.message) || _t("Warning"),
            subtitle: error.data.title,
            $content: $(QWeb.render('CrashManager.warning', {error: error}))
        }).open();
    },
    show_error: function(error) {
        if (!this.active) {
            return;
        }
        error.message = "Alert"
        //error.message = error.message && error.message.replace("Odoo", "")
        var dialog = new Dialog(this, {
            title: _.str.capitalize(error.type || error.message) || _t("Warning"),
            $content: $(QWeb.render('CrashManager.error', {error: error}))
        });
        console.log(error)
        // When the dialog opens, initialize the copy feature and destroy it when the dialog is closed
        var $clipboardBtn;
        var clipboard;
        dialog.opened(function () {
            // When the full traceback is shown, scroll it to the end (useful for better python error reporting)
            dialog.$(".o_error_detail").on("shown.bs.collapse", function (e) {
                e.target.scrollTop = e.target.scrollHeight;
            });

            $clipboardBtn = dialog.$(".o_clipboard_button");
            $clipboardBtn.tooltip({title: _t("Copied !"), trigger: "manual", placement: "left"});
            clipboard = new window.Clipboard($clipboardBtn[0], {
                text: function () {
                    return (_t("Warning") + ":\n" + error.message + "\n\n" + error.data.debug).trim();
                }
            });
            clipboard.on("success", function (e) {
                _.defer(function () {
                    $clipboardBtn.tooltip("show");
                    _.delay(function () {
                        $clipboardBtn.tooltip("hide");
                    }, 800);
                });
            });
        });
        dialog.on("closed", this, function () {
            $clipboardBtn.tooltip("destroy");
            clipboard.destroy();
        });

        dialog.open();
    },
    show_message: function(exception) {
        this.show_error({
            type: _t("Alert"),
            message: exception,
            data: {debug: ""}
        });
    },
});

Dialog.include({
    init: function (parent, options) {
        this._super(parent);
        this._opened = $.Deferred();
        // Normal Odoo dialogues have title Odoo followed by subtitle, Replace it
        options = _.defaults(options || {}, {
            title: _t(''), subtitle: '',
            size: 'large',
            dialogClass: '',
            $content: false,
            buttons: [{text: _t("Ok"), close: true}],
            technical: true,
        });

        this.$content = options.$content;
        this.title = options.title;
        this.subtitle = options.subtitle;
        this.dialogClass = options.dialogClass;
        this.size = options.size;
        this.buttons = options.buttons;
        this.technical = options.technical;
    },
});

WebClient.include({
    bind_events: function () {
        var self = this;
        $('.oe_systray').show();
        this.$el.on('mouseenter', '.oe_systray > div:not([data-toggle=tooltip])', function () {
            $(this).attr('data-toggle', 'tooltip').tooltip().trigger('mouseenter');
        });
        this.$el.on('click', '.oe_dropdown_toggle', function (ev) {
            ev.preventDefault();
            var $toggle = $(this);
            var doc_width = $(document).width();
            var $menu = $toggle.siblings('.oe_dropdown_menu');
            $menu = $menu.size() >= 1 ? $menu : $toggle.find('.oe_dropdown_menu');
            var state = $menu.is('.oe_opened');
            setTimeout(function () {
                // Do not alter propagation
                $toggle.add($menu).toggleClass('oe_opened', !state);
                if (!state) {
                    // Move $menu if outside window's  edge
                    var offset = $menu.offset();
                    var menu_width = $menu.width();
                    var x = doc_width - offset.left - menu_width - 2;
                    if (x < 0) {
                        $menu.offset({ left: offset.left + x }).width(menu_width);
                    }
                }
            }, 0);
        });
        core.bus.on('click', this, function (ev) {
            $('.tooltip').remove();
            if (!$(ev.target).is('input[type=file]')) {
                self.$('.oe_dropdown_menu.oe_opened, .oe_dropdown_toggle.oe_opened').removeClass('oe_opened');
            }
        });
        core.bus.on('connection_lost', this, this.on_connection_lost);
        core.bus.on('connection_restored', this, this.on_connection_restored);

        // crash manager integration
        core.bus.on('rpc_error', crash_manager, crash_manager.rpc_error);
        window.onerror = function (message, file, line, col, error) {
            // Scripts injected in DOM (eg: google API's js files) won't return a clean error on window.onerror.
            // The browser will just give you a 'Script error.' as message and nothing else for security issue.
            // To enable onerror to work properly with CORS file, you should:
            //   1. add crossorigin="anonymous" to your <script> tag loading the file
            //   2. enabling 'Access-Control-Allow-Origin' on the server serving the file.
            // Since in some case it wont be possible to to this, this handle should have the possibility to be
            // handled by the script manipulating the injected file. For this, you will use window.onOriginError
            // If it is not handled, we should display something clearer than the common crash_manager error dialog
            // since it won't show anything except "Script error."
            // This link will probably explain it better: https://blog.sentry.io/2016/05/17/what-is-script-error.html
            if (message === "Script error." && !file && !line && !col && !error) {
                if (window.onOriginError) {
                    window.onOriginError();
                    delete window.onOriginError;
                } else {
                    crash_manager.show_error({
                        type: _t("Alert"),
                        message: _t("Unknown CORS error"),
                        data: {debug: _t("An unknown CORS error occured. The error probably originates from a JavaScript file served from a different origin.")},
                    });
                }
            } else {
                var traceback = error ? error.stack : '';
                crash_manager.show_error({
                    type: _t("Alert"),
                    message: message,
                    data: {debug: file + ':' + line + "\n" + _t('Traceback:') + "\n" + traceback},
                });
            }
        };
    },
});

SearchView.include({
    start: function () {
        if (this.headless) {
            this.do_hide();
        }
        this.toggle_visibility(false);
        this.setup_global_completion();
        this.query = new SearchView.SearchQuery()
                .on('add change reset remove', this.proxy('do_search'))
                .on('change', this.proxy('renderChangedFacets'))
                .on('add reset remove', this.proxy('renderFacets'));
        this.$('.o_searchview_more')
            .toggleClass('fa-search-plus', this.visible_filters)
            .toggleClass('fa-search-minus', !this.visible_filters);
        var menu_defs = [];
        this.prepare_search_inputs();
        if (this.$buttons) {
            if (!this.options.disable_filters) {
                this.filter_menu = new FilterMenu(this, this.filters, this.fields);
                menu_defs.push(this.filter_menu.appendTo(this.$buttons));
            }
            if (!this.options.disable_groupby) {
                this.groupby_menu = new GroupByMenu(this, this.groupbys, this.fields);
                menu_defs.push(this.groupby_menu.appendTo(this.$buttons));
            }
            if (!this.options.disable_favorites) {
                this.favorite_menu = new FavoriteMenu(this, this.query, this.dataset.model, this.action_id, this.favorite_filters);
                menu_defs.push(this.favorite_menu.appendTo(this.$buttons));
            }
        }
        return $.when.apply($, menu_defs).then(this.set_default_filters.bind(this));
    },
});

});
