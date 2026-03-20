# Bookmarklet

## Dark mode style inspired by [Claude](https://platform.claude.com/docs/)

Color references

```
bg: #262624
fg: #C2C0B6
title: #FAF9F5
card-bg: #30302E
card-fg: #F3F7F6
dark-bg: #1F1E1D
border: #42413E
link: #D97757
```

Copy the js to the bookmark

```
javascript:(function(){var s=document.createElement('style');s.id='claude-dark-bm';if(document.getElementById('claude-dark-bm')){document.getElementById('claude-dark-bm').remove();return;}s.textContent='html,body,.page-wrapper,.w-nav,.section,.container{background:#262624!important;color:#C2C0B6!important;scrollbar-color:#4A4A46 #262624}h1,h2,h3,h4,h5,h6{color:#FAF9F5!important}.nav-link,.navbar,.w-nav-link,.sidebar{background:#1F1E1D!important;color:#C2C0B6!important}p,li,span,div{color:#C2C0B6!important}a{color:#D97757!important}a:hover{color:#D97757!important}.card,div[class*="card"],div[class*="case"],.highlight{background:#30302E!important;border:1px solid #4A4A46!important}code{background:#30302E!important}footer,.footer,.w-nav{background:#1F1E1D!important}input,textarea,select{background:#30302E!important;color:#F3F7F6!important;border-color:#42413E!important}';document.head.appendChild(s);document.documentElement.style.backgroundColor='#262624';})();
```
