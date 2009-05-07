function addRow(content,morecontent)
{
         if (!document.getElementsByTagName) return;
         tabBody=document.getElementsByTagName("TBODY").item(0);
         row=document.createElement("TR");
         cell1 = document.createElement("TD");
         cell2 = document.createElement("TD");
         textnode1=document.createTextNode(content);
         textnode2=document.createTextNode(morecontent);
         cell1.appendChild(textnode1);
         cell2.appendChild(textnode2);
         row.appendChild(cell1);
         row.appendChild(cell2);
         tabBody.appendChild(row);
       
   
}