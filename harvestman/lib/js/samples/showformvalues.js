var displayWindow = window.open();

function showFormValues(form ) { 
    displayWindow.document.write('Form:');
    displayWindow.document.write(form.name);
    displayWindow.document.write('<br>');

    var formElements = form.getElementsByTagName('input');

    for (var i = 0; i < formElements.length; i++){
        var element = formElements[i];
        
        displayWindow.document.write(element.name + ' :  ' + element.value + ' <br>');}} 

Array.forEach(document.forms, showFormValues);
