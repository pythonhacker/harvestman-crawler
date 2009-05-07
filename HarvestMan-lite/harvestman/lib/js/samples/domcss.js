function includeCSS(p_file) {
        var v_css  = document.createElement('link');
        v_css.rel = 'stylesheet'
        v_css.type = 'text/css';
        v_css.href = p_file;
        document.getElementsByTagName('head')[0].appendChild(v_css);
}
