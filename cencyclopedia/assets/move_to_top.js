var oldHref = document.location.href;

// https://stackoverflow.com/questions/3522090/event-when-window-location-href-changes
window.onload = function() {
    var bodyList = document.querySelector('body');
    var observer = new MutationObserver(function(mutations) {
      if (oldHref != document.location.href) {
        oldHref = document.location.href;
        // https://www.xjavascript.com/blog/how-to-scroll-to-top-of-page-with-javascript-jquery/
        window.scrollTo(0, 0);
      }
    });

    var config = { childList: true, subtree: true};
    observer.observe(bodyList, config);
};
