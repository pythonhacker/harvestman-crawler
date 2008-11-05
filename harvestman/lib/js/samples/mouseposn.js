function showit()
{
   document.forms['theform'].xcoord.value=event.x;
   document.getElementById('spanx').innerHTML='x='+event.x;
   document.forms.theform.ycoord.value=event.y;
   document.getElementById('spany').innerHTML='y='+event.y;
}
function showitMOZ(e)
{
   document.forms['theform'].xcoord.value=e.pageX;
   document.getElementById('spanx').innerHTML='x='+e.pageX;
   document.getElementById('spany').innerHTML='y='+e.pageY;
   document.forms.theform.ycoord.value=e.pageY;
}
if (!document.all){
window.captureEvents(Event.CLICK);
window.onclick=showitMOZ;
}
else
{
document.onclick=showit;
}