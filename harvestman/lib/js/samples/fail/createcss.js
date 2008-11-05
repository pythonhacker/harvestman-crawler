function createCSS(selector, declaration) {
        // test for IE
        var ua = navigator.userAgent.toLowerCase();
        var isIE = (/msie/.test(ua)) && !(/opera/.test(ua)) && (/win/.test(ua));

        // create the style node for all browsers
        var style_node = document.createElement("style");
        style_node.setAttribute("type", "text/css");
        style_node.setAttribute("media", "screen"); 

        // append a rule for good browsers
        if (!isIE) style_node.appendChild(document.createTextNode(selector + " {" + declaration + "}"));

        // append the style node
        document.getElementsByTagName("head")[0].appendChild(style_node);

        // use alternative methods for IE
        if (isIE && document.styleSheets && document.styleSheets.length > 0) {
                var last_style_node = document.styleSheets[document.styleSheets.length - 1];
                if (typeof(last_style_node.addRule) == "object") last_style_node.addRule(selector, declaration);
        }
};