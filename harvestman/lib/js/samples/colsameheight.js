function setH()
{
   var maxH = Math.max(document.getElementById('leftside').offsetHeight,document.getElementById('rightside').offsetHeight);
   document.getElementById('leftside').style.height=maxH+'px';
   document.getElementById('rightside').style.height=maxH+'px';
}
onload=setH;