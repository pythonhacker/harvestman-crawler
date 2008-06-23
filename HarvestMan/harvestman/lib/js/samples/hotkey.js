var key1="32";
var x='';
function handler(e) 
{
  if (document.all) {
  var evnt = window.event; 
  x=evnt.keyCode;
}
else
x=e.charCode;
if (x==key1) location.href='http://www.expertsrt.com';
}
if (!document.all){
window.captureEvents(Event.KEYPRESS);
window.onkeypress=handler;
}
else
{
document.onkeypress = handler;
} 
