function SendSelectValueToTextArea(selectValue,targetTextArea)
{
   var txtNode=document.createTextNode(selectValue);
   var textArea=document.getElementById(targetTextArea);
   textArea.appendChild(txtNode);
}