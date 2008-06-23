function gm_showXPath()
{
        var win = window.open("", window.location, "width="+700+",height="+300+",menubar=no,toolbar=no,directories=no,scrollbars=yes,status=no,left=0,top=0,resizable=yes");
        var xpathInfo = "";     
        var elt = null;
        var links = document.getElementsByTagName('a');
        var inputs = document.getElementsByTagName('input');
        // add click events
        xpathInfo +=  "<h2>" + window.location + "</h2>";
        for (var i=0; i < links.length; i++)
        {
                elt = links[i];
                var id = elt.getAttribute('id');
                if (id != "gm_showxpath")
                {
                        xpathInfo += "href=" + elt.getAttribute('href') + ",xpath="+getElementXPath(links[i]);
                        xpathInfo += "<br>";
                }
        }
        
        for (var j=0; j < inputs.length; j++)
        {
                elt = inputs[j];
                var type = elt.getAttribute('type');
                if (type != null && type.toLowerCase() == 'submit')
                {
                        xpathInfo += "href=" + elt.getAttribute('href') + ",xpath="+getElementXPath(links[i]);
                        xpathInfo += "<br>";
                }
        }
        
        win.document.write(xpathInfo);
        win.document.close();
}
