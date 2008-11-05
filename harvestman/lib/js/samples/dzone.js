var sharedURL='';  // Place your url between the quotes.

function getFeed(url, callback) {
   var newScript = document.createElement('script');
       newScript.type = 'text/javascript';
       newScript.src = 'http://pipes.yahoo.com/pipes/9oyONQzA2xGOkM4FqGIyXQ/run?&_render=JSON&_callback='+callback+'&feed=' + sharedURL;
   document.getElementsByTagName("head")[0].appendChild(newScript);
}

function dzone(feed) {
   var tmp='';
   for (var i=0; i<feed.value.items.length; i++) {
      tmp+='<a href="'+feed.value.items[i].link+'" rel="nofollow">';
      tmp+=feed.value.items[i].title+'</a><br>';
   }
   document.getElementById('dzoneLinks').innerHTML=tmp;
}

getFeed(sharedURL, 'dzone');
