# Bookmarklet

Each of the bookmarklets can toggle a custom comfort mode in the browser.

## Dark mode

Colors
- Text: #9e9e9e ([Claude docs](https://platform.claude.com/docs/) text color)
- Lighter text: #cecece

```
javascript:(function(){const id='comfort-mode';const existing=document.getElementById(id);if(existing){existing.remove();return;}const style=document.createElement('style');style.id=id;style.textContent=`body,p,div:not(.md-code-block){color:#9e9e9e!important}h1,h2,h3,h4,h5,h6,strong,input,textarea{color:#cecece!important}`;document.head.appendChild(style);})();
```

### chat.deepseek.com

Header
- `.the-header`

Footer
- `._871cbca`: container
- `.d72636e2`: empty container for the gap strip
- `_0fcaa63`: "AI-generated, for reference only" caption

Markdown
- `_9bc997d`: span that fills the current color for the code block bg, revealed by bottom corners

Colors
- Background: #1f1f20 (Adjusted based on Claude's background #1f1f1e given Deepseek's colors are tinted towards blue, e.g., side bar #1b1b1c)

```
javascript:(function(){var id='comfort-mode';var ex=document.getElementById(id);if(ex){ex.remove();return;}var s=document.createElement('style');s.id=id;s.textContent=`body,html,.the-header,._871cbca,.d72636e2,._0fcaa63{background-color:#1f1f20!important;background-image:none!important}._9bc997d{color:#1f1f20!important}body,p{color:#9e9e9e!important}h1,h2,h3,h4,h5,h6,strong{color:#cecece!important}`;document.head.appendChild(s);})();
```

## Light mode

Colors
- Background: #B9D9EB ([Columbia blue](https://en.wikipedia.org/wiki/Columbia_blue))

```
javascript:(function(){const id='comfort-mode';const existing=document.getElementById(id);if(existing){existing.remove();return;}const style=document.createElement('style');style.id=id;style.textContent='html,body,.page-wrapper,.w-nav,.section,.container,section{background:#B9D9EB!important;scrollbar-color:#A0A0A0 #00000000!important;}#thread-bottom-container,#thread-bottom-container::before,#thread-bottom-container::after{background:#B9D9EB!important;}';document.head.appendChild(style);})();
```

