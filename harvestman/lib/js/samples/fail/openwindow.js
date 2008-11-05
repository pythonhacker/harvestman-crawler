function openAWindow( pageToLoad, winName, width, height, center)
{
    xposition=0; yposition=0;
    if ((parseInt(navigator.appVersion) >= 4 ) && (center)){
        xposition = (screen.width - width) / 2;
        yposition = (screen.height - height) / 2;
    }
        
        //0 => no
        //1 => yes
    var args = "";
        args += "width=" + width + "," + "height=" + height + ","
                + "location=0,"
                + "menubar=0,"
                + "resizable=0,"
                + "scrollbars=0,"
                + "statusbar=false,dependent,alwaysraised,"
                + "status=false,"
                + "titlebar=no,"
                + "toolbar=0,"
                + "hotkeys=0,"
                + "screenx=" + xposition + ","  //NN Only
                + "screeny=" + yposition + ","  //NN Only
                + "left=" + xposition + ","     //IE Only
                + "top=" + yposition;           //IE Only
                //fullscreen=yes, add for full screen
        // var dmcaWin = window.open(pageToLoad,winName,args );
        // dmcaWin.focus();
    //window.showModalDialog(pageToLoad,"","dialogWidth:650px;dialogHeight:500px");
}
