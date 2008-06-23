function selectiveTotal(form, which)
{
        var total = 0;
        for(var j = 0; j < form.elements.length; j++){
                var cid = form.elements[j].id.toString();
                if ((form.elements[j].type == "text") && 
                    (form.elements[j].value.length > 0) && 
                    (cid.charAt(cid.length-1) == which) && 
                    (cid != "total" + which))
                {
                        total += parseInt(form.elements[j].value);
                }
        }
        document.getElementById("total" + which).value = total;
        totalTheTotals("1","2","3");
}

function totalTheTotals(a, b, c)
{
        var total = parseInt(document.getElementById("total" + a).value) + parseInt(document.getElementById("total" + b).value);
        document.getElementById("total" + c).value = total;
}