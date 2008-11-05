var str='';
var obj='false';
var pntr='';
var cnt=0;
var textArr = new Array(5);
textArr[0] = "All your bases are belong to us!";
textArr[1] = "The answer is 42; of course.";
textArr[2] = "The end of the universe will be the result of a mis-calculation in the core.";
textArr[3] = "I don't believe its alive; but it thinks it is.";
textArr[4] = "About 10 seconds after you open it; you'll wish you hadn't";

function looptext()
{
   obj.innerHTML=str.substr(0,cnt);
   cnt++;
   if (cnt<=str.length) setTimeout('looptext()',100);
}

function typeText(lnk,lyr)
{
   str=textArr[lyr];
   pntr= 'lyr'+lyr;
   obj=document.getElementById(pntr);
   obj.style.left=(lnk.offsetLeft+30)+'px';
   obj.style.top=(lnk.offsetTop+25)+'px';
   obj.style.display='block';
   cnt=1;
   looptext();
}

function clearText(lyr)
{
   cnt=2500;
   pntr='lyr'+lyr;
   obj=document.getElementById(pntr);
   obj.style.display='none';
   obj.style.left='-50px';
   obj.style.top='-50px';
   obj.innerHTML='&nbsp;';
}