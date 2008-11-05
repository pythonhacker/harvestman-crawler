var count1 = 0;
var count2 = 0;

function insertOptionBefore(num)
{
  var elSel = document.getElementById('selectX');
  if (elSel.selectedIndex >= 0) {
    var elOptNew = document.createElement('option');
    elOptNew.text = 'Insert' + num;
    elOptNew.value = 'insert' + num;
    var elOptOld = elSel.options[elSel.selectedIndex];  
    try {
      elSel.add(elOptNew, elOptOld); // standards compliant; doesn't work in IE
    }
    catch(ex) {
      elSel.add(elOptNew, elSel.selectedIndex); // IE only
    }
  }
}

function removeOptionSelected()
{
  var elSel = document.getElementById('selectX');
  var i;
  for (i = elSel.length - 1; i>=0; i--) {
    if (elSel.options[i].selected) {
      elSel.remove(i);
    }
  }
}

function appendOptionLast(num)
{
  var elOptNew = document.createElement('option');
  elOptNew.text = 'Append' + num;
  elOptNew.value = 'append' + num;
  var elSel = document.getElementById('selectX');

  try {
    elSel.add(elOptNew, null); // standards compliant; doesn't work in IE
  }
  catch(ex) {
    elSel.add(elOptNew); // IE only
  }
}

function removeOptionLast()
{
  var elSel = document.getElementById('selectX');
  if (elSel.length > 0)
  {
    elSel.remove(elSel.length - 1);
  }
}