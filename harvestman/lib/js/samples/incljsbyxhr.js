function include(jsFileLocation)
{
        if(window.XMLHttpRequest)
        {
                var req = new XMLHttpRequest();
        }
        else
        {
                var req = new ActiveXObject("Microsoft.XMLHTTP");
        }
        req.open("GET", jsFileLocation,false);
        req.onreadystatechange = function()
        {
                if (req.readyState == 4)
                {
                        window.eval(req.responseText);
                }
        }
        req.send(null);
}
