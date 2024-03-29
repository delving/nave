/*!
 * @copyright &copy; Kartik Visweswaran, Krajee.com, 2014
 * @version 1.0.0
 *
 * Bootstrap Popover Extended - Popover with modal behavior, styling enhancements and more.
 *
 * For more JQuery/Bootstrap plugins and demos visit http://plugins.krajee.com
 * For more Yii related demos visit http://demos.krajee.com
 */
!function ($) {

    var PopoverX = function (element, options) {
        var self = this;
        self.options = options;
        self.$element = $(element).on('click.dismiss.popoverX', '[data-dismiss="popover-x"]', $.proxy(self.hide, self));
        self.init();
    };

    PopoverX.prototype = $.extend({}, $.fn.modal.Constructor.prototype, {
        constructor: PopoverX,
        init: function () {
            var self = this;
            self.$body = $(document.body);
            self.$target = self.options.$target;
            if (self.$element.find('.popover-footer').length) {
                self.$element
                    .removeClass('has-footer')
                    .addClass('has-footer');
            }
            if (self.options.remote) {
                self.$element.find('.popover-content').load(self.options.remote, function () {
                    self.$element.trigger('load.complete.popoverX');
                });
            }
        },
        getPosition: function () {
            var $element = this.$target;
            return $.extend({}, ($element.position()), {
                width: $element[0].offsetWidth, height: $element[0].offsetHeight
            });
        },
        refreshPosition: function () {
            var self = this, $dialog = self.$element, placement = self.options.placement,
                actualWidth = $dialog[0].offsetWidth, actualHeight = $dialog[0].offsetHeight,
                position, pos = self.getPosition();
            switch (placement) {
                case 'bottom':
                    position = {top: pos.top + pos.height, left: pos.left + pos.width / 2 - actualWidth / 2};
                    break;
                case 'top':
                    position = {top: pos.top - actualHeight, left: pos.left + pos.width / 2 - actualWidth / 2};
                    break;
                case 'left':
                    position = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left - actualWidth};
                    break;
                case 'right':
                    position = {top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left + pos.width};
                    break;
            }
            $dialog
                .css(position)
                .addClass(placement)
                .addClass('in');
        },
        show: function () {
            var self = this, $dialog = self.$element;
            $dialog.css({ top: 0, left: 0, display: 'block', 'z-index': 1050 });
            self.refreshPosition();
            $.fn.modal.Constructor.prototype.show.call(self, arguments);
        }
    });

    $.fn.popoverX = function (option) {
        var self = this;
        return self.each(function () {
            var $this = $(this);
            var data = $this.data('popover-x');
            var options = $.extend({}, $.fn.popoverX.defaults, $this.data(), typeof option == 'object' && option);
            if (!options['$target']) {
                if (data && data.$target) {
                    options['$target'] = data.$target;
                } else {
                    options['$target'] = option.$target || $(option.target);
                }
            }
            if (!data) {
                $this.data('popover-x', (data = new PopoverX(this, options)))
            }

            if (typeof option == 'string') {
                data[option]()
            }
        });
    };

    $.fn.popoverX.defaults = $.extend({}, $.fn.modal.defaults, {
        placement: 'right',
        keyboard: true
    });

    $(document).on('ready', function () {
        $("[data-toggle='popover-x']").on('click', function (e) {
            var $this = $(this), href = $this.attr('href'),
                $dialog = $($this.attr('data-target') || (href && href.replace(/.*(?=#[^\s]+$)/, ''))), //strip for ie7
                option = $dialog.data('popover-x') ? 'toggle' : $.extend({ remote: !/#/.test(href) && href }, $dialog.data(), $this.data());
            e.preventDefault();
            $dialog.trigger('click.target.popoverX');
            if (option !== 'toggle') {
                option['$target'] = $this;
                $dialog
                    .popoverX(option)
                    .popoverX('show')
                    .on('hide', function () {
                        $this.focus()
                    });
            }
            else {
                $dialog
                    .popoverX(option)
                    .on('hide', function () {
                        $this.focus()
                    });
            }
        });

        $('[data-toggle="popover-x"]').on('keyup', function (e) {
            var $this = $(this),
                $dialog = $($this.attr('data-target') || (href && href.replace(/.*(?=#[^\s]+$)/, ''))); //strip for ie7
            $dialog && e.which == 27 && $dialog.trigger('keyup.target.popoverX') && $dialog.popoverX('hide');
        });
    });
}(window.jQuery);