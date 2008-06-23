//<![CDATA[
// updateForm() and cleanMe() for cleanPaperFilename
// 2007 by Sascha Tayefeh
//
// Problem: How to cope with tons of papers to store? 
// Solution: Give them systemantic, human-readable filenames.
// Syntax: author__title__mag_vol_year.pdf
//
// rules: 
// * Author is turned to lowercase (easier to find where searching
//   is case sensitive)
// * All non-alphanumeric-characters in the title will be turned
//   either into '_' or deleted.
// * Append the magazine-abbev., the volume and the year - and 
//   celebrate
//

function cleanMe(unpure)
{
   var pure=unpure.replace(/[\s]/g,'_'); // First, replace all white-spaces by a single '_'
   pure=pure.replace(/[^_\d\w\-]/g,''); // Next, replace all invalid characters
   pure=pure.replace(/__*/g,'_'); // Clean up multiple '_'
   return pure;

}

function startForm()
{
        if(document.getElementById('npUpdate').checked) t=setTimeout('updateForm()',100);
        else t=setTimeout('startForm()',200);
}

function npReset()
{
 document.getElementById('title').value
   =document.getElementById('author').value
   =document.getElementById('mag').value
   =document.getElementById('vol').value
   =document.getElementById('pubYear').value
   ='';
   
}

function updateForm()
{
   var green='#6f6';
   var red='#f66';
   var blue='#ccf';
   var grey='#ccc';

   var title=document.getElementById('title').value; // NOT .innerHTML, but actualle .value for textarea
   var author=document.getElementById('author').value;
   var mag=document.getElementById('mag').value;
   var vol=document.getElementById('vol').value;
   var pubYear=document.getElementById('pubYear').value;
   var output='';


   if (author) 
   {
      author=cleanMe(author).toLowerCase()+'__';
      document.getElementById('author').style.backgroundColor=green;
   } else document.getElementById('author').style.backgroundColor=grey;

   if (title) 
   {
      document.getElementById('title').style.backgroundColor=green;
      title=cleanMe(title)+"__";
   } else document.getElementById('title').style.backgroundColor=grey;

   if (mag) 
   {
      mag=cleanMe(mag)+"_";
      document.getElementById('mag').style.backgroundColor=green;
   } else document.getElementById('mag').style.backgroundColor=grey;

   if (vol && vol.match(/^\d+$/g) ) 
   {
      vol=vol+"_"; 
      document.getElementById('vol').style.backgroundColor=green; 
   } else if (vol && ! vol.match(/d+$/g) )
   { 
      vol=''; 
      document.getElementById('vol').style.backgroundColor=red; 
   } else document.getElementById('vol').style.backgroundColor=grey;

   if (pubYear && pubYear.match(/^\d+$/g) ) 
   {
      pubYear=pubYear+"_";
      document.getElementById('pubYear').style.backgroundColor=green; 
   }
   else if (pubYear && ! pubYear.match(/d+$/g) )
   { 
      pubYear=''; 
      document.getElementById('pubYear').style.backgroundColor=red; 
   } else document.getElementById('pubYear').style.backgroundColor=grey;

   // Assemble the filename string
   output=author +  title + mag  + vol + pubYear + '.pdf';

   if(output!='.pdf')
   {
      document.getElementById('output').innerHTML=output;
      document.getElementById('output').style.backgroundColor=blue;
   } else { 
      document.getElementById('output').innerHTML='';
      document.getElementById('output').style.backgroundColor=grey;
   }

  if(document.getElementById('npUpdate').checked) t=setTimeout('updateForm()',100);
  else t=setTimeout('startForm()',200);
}

