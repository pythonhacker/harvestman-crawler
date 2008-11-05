onload = function() {
      var divs = document.getElementsByTagName('div');
      for(var i=0; i<divs.length; i++) {
        if(divs[i].className == 'regular' && divs[i].innerHTML.match(/\(via.*Twitter\s\//)) {
          divs[i].className = 'quote';
          var q = divs[i].innerHTML;
          var t = q.replace(/^\s*.*?:/, '').replace(/\(via [^\)]+\)/, '');
          size = (t.length > 75) ? 'medium' : 'short';
          try {
            divs[i].innerHTML = '<div class="quote_text"><span class="' + size + '">' + t + '</span></div><div class="source">' + q.match(/\((via [^\)]+)\)/)[1] + '</div>';
          } catch(e) {}
        }
      }
    }
