/*
* moaModal
* MIT Licensed
* @author Mamod Mehyar
* http://sweefty.com/moaModal
* http://sweefty.com
* version : 2.0.0
*/
(function(b){var m,h,r,n={speed:500,easing:"linear",position:"0 auto",animation:"none",on:"click",escapeClose:!0,overlayColor:"#000000",overlayOpacity:.7,overlayClose:!0};b(function(){m=b("<div></div>").css({width:"100%",height:b(document).height(),position:"fixed",backgroundColor:"#000",overflow:"hidden",opacity:.7,top:0,left:0,display:"none",zIndex:"999996"}).appendTo("body");h=b("<div></div>").css({width:"100%",height:b(document).height(),position:"absolute",display:"none",overflow:"hidden",top:0, left:0,zIndex:"999998"}).appendTo("body");r=b("<div></div>").css({position:"relative",width:"100%",zIndex:"999997",top:0,left:0,visibility:"hidden"}).appendTo(h)});var t=function(d,a){a=b.extend({},n,a);var c=b(a.modal);if(c.length){a.position=a.position.replace(/(\d+)(\s|$)/g,"$1px$2");var g=r,p={position:"relative",overflow:"hidden",display:"block",zIndex:"999999",margin:a.position},e=c.clone(),k;e.appendTo("body").css({maxWidth:window.screen.width,maxHeight:window.screen.height});e.outerWidth(); k=e.outerHeight();0===k&&(k="1%");e.remove();for(var l={},e=a.animation.split(" "),q=0;q<e.length;q++)l[e[q]]=!0;!1!==a.overlayClose&&h.click(function(a){this!==a.target&&a.target!==g[0]||c.trigger("close.modal")});if(a.escapeClose)b(document).on("keydown.modal",function(a){27===a.which&&c.trigger("close")});a.close&&b(a.close).click(function(){c.trigger("close.modal");return!1});d.on(a.on,function(){m.css({backgroundColor:a.overlayColor,opacity:a.overlayOpacity,height:b(document).height()});if("click"!== a.on)b(document).one("mouseup",function(a){});var f;"center"===a.position?(f=b(window).height()/2-k/2,p.margin=f+"px auto"):"bottom"===a.position&&(f=b(window).height()-k,p.margin=f+"px auto");g.children(":first").hide().appendTo("body");c.appendTo(g);h.css({height:b(document).height(),width:"100%",display:"block"});var d=0,e=b(window).scrollTop();c.css(p);!0===l.top?e=-(k+parseInt(c.css("marginTop"))-b(window).scrollTop()):!0===l.bottom&&(e=b(window).height()+b(window).scrollTop());!0===l.left?(f= parseInt(c.css("marginLeft")),isNaN(f)&&(f=g.width()/2-c.width()/2),d=-(c.width()+f)):!0===l.right&&(f=parseInt(c.css("marginLeft")),isNaN(f)&&(f=g.width()/2-c.width()/2),d=g.width()-f);c.on("close.modal",function(){g.stop().animate({top:e,left:d,opacity:0},{duration:a.speed,easing:"linear",complete:function(){h.css({top:0,position:"absolute"})}});m.fadeOut(a.speed+100,function(){g.css({visibility:"hidden",top:0,left:0});h.hide()});c.off("close.modal")});m.stop().fadeIn(a.speed,function(){});g.css({top:e, left:d,opacity:0,visibility:"visible"}).stop().animate({opacity:1,top:b(window).scrollTop(),left:0},{easing:a.easing,duration:a.speed,complete:function(){h.css({top:-b(window).scrollTop(),position:"fixed"});a.complete&&"function"===typeof a.complete&&a.complete()}});return!1})}};b.fn.modal=function(d,a){a||"object"!==typeof d||(a=d,d=void 0);var c=b.extend({},n,a);c.modal=c.target;if("view"===d)c.modal=this,c.on="view.modal";else if("close"===d)return this.trigger("close.modal"),!1;return this.each(function(){var a= b(this);a[0]===b(document)[0]?n=c:(t(a,c),a.trigger("view.modal"))})}})(jQuery);