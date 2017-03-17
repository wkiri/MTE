define([
    'Constants',
    'Dispatcher',
    'MTEInterface',
    'AutoCompletion',
    'MTEListener'
], function (
    CONSTANTS,
    Dispatcher,
    MTEInterface,
    AutoCompletion,
    MTEListener
) {
    "use strict";

    var MTEViewer = function (options) {
        var mteViewer = this;
        mteViewer._cgiRoot = options.cgiRoot;
        mteViewer._containerId = options.containerId;
        mteViewer._thumbnailUrlRoot = options.thumbnailUrlRoot;
        mteViewer._mmgisUrlRoot = options.mmgisUrlRoot;
        mteViewer._mslANLinkRoot = options.mslANLinkRoot;
        mteViewer._currentUrl = location.href;
        mteViewer._autoCompletionList = [];
        mteViewer._interface = new MTEInterface(mteViewer._containerId, mteViewer._thumbnailUrlRoot, mteViewer._mslANLinkRoot);
        mteViewer._autoCompletion = new AutoCompletion(mteViewer._cgiRoot);
        mteViewer._listeners = new MTEListener(mteViewer._interface, mteViewer._autoCompletion, mteViewer._cgiRoot, mteViewer._mmgisUrlRoot);
        mteViewer._interface.build();
        mteViewer._autoCompletion.enable(mteViewer._interface._inputField);
        mteViewer._listeners.initEventListeners();

        $(document).ready(function () {
            dispatch(mteViewer._currentUrl);
        });
    }

    function dispatch (url) {
        var disp = new Dispatcher(url);
        if (disp.getDispViewStr() === CONSTANTS.LOOKUP_VIEW) {
            popupView(disp);
        }
    }

    //e.x. http://mte.jpl.nasa.gov?lookup=Windjana
    function popupView (disp) {
        var partialUrl = disp.getPartialURL();
        var targetName = disp.getParameterTargetName();

        //hide the parameters associated with the URL for security purposes.
        window.history.pushState("", "", partialUrl);

        //TODO this is a very bad practice!!!use PROMISE should resolve the problem.
        setTimeout(function () {
            var searchInput = document.getElementById("mteSearchInput");
            searchInput.value = targetName;
            var searchButton = document.getElementById("searchButton");
            $(searchButton).click();
            setTimeout(function () {
                var targetNameDiv = document.getElementById(targetName);
                $(targetNameDiv).click();
            }, 1000)
        }, 1000);
    }

    return MTEViewer;
});