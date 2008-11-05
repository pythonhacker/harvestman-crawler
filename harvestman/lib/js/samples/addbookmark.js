var bookmarkurl="Add full URI here"
var bookmarktitle="Add your title here"

function addbookmark(){
if (document.all)
window.external.AddFavorite(bookmarkurl,bookmarktitle)//IE
window.sidebar.addPanel( bookmarktitle, bookmarkurl, '' );//Moz
}