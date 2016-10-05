require([
    'MTEViewer'
], function (
    MTEViewer
){
    "use strict";

    $.getJSON("configuration.json", function (config) {
        var cgiRoot = config.cgi_root;
        var thumbnailUrlRoot = config.thumnail_url_root;
        var mslANLinkRoot = config.msl_an_link_root;
        var containerId = "mteContainer";
        new MTEViewer({
            containerId: containerId,
            cgiRoot: cgiRoot,
            thumbnailUrlRoot: thumbnailUrlRoot,
            mslANLinkRoot: mslANLinkRoot
        })
    });
});