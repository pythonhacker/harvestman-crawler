function ProgressIndicator(element, options) {
        var element = $(element);
        var my_options = {show:Element.show, hide:Element.hide};
        Object.extend(my_options, options || {});
        this.show = function() { my_options.show(element) }
        this.hide = function() { my_options.hide(element) }
        this.hide();
}
