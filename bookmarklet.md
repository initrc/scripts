# Bookmarklet

Each of the bookmarklets can toggle a custom comfort mode in the browser.

## Dark mode

Colors
- Text: #9e9e9e ([Claude docs](https://platform.claude.com/docs/) text color)
- Lighter text: #cecece

```
javascript:(function(){const id='comfort-mode';const existing=document.getElementById(id);if(existing){existing.remove();return;}const style=document.createElement('style');style.id=id;style.textContent=`body,p,div:not(.md-code-block){color:#9e9e9e!important}h1,h2,h3,h4,h5,h6,strong,input,textarea{color:#cecece!important}`;document.head.appendChild(style);})();
```

## Light mode

Colors
- Background: #B9D9EB ([Columbia blue](https://en.wikipedia.org/wiki/Columbia_blue))

```
javascript:(function(){const id='comfort-mode';const existing=document.getElementById(id);if(existing){existing.remove();return;}const style=document.createElement('style');style.id=id;style.textContent='html,body,.page-wrapper,.w-nav,.section,.container,section{background:#B9D9EB!important;scrollbar-color:#A0A0A0 #00000000!important;}#thread-bottom-container,#thread-bottom-container::before,#thread-bottom-container::after{background:#B9D9EB!important;}';document.head.appendChild(style);})();
```

