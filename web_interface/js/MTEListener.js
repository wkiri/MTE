define([
    'MTEHandler',
    'Util'
], function (
    MTEHandler,
    Util
){
    "use strict";

    var MTEListener = function (mteInterface, autoCompletion, cgiRoot, mmgisUrlRoot) {
        this._handlers = new MTEHandler();
        this._interface = mteInterface;
        this._autoCompletion = autoCompletion;
        this._cgiRoot = cgiRoot;
        this._mmgisUrlRoot = mmgisUrlRoot;
        this._util = new Util();
    }

    MTEListener.prototype.initEventListeners = function () {
        searchEventListener(this._interface, this._autoCompletion, this._handlers.searchHandler,
            this._handlers.enterHandler, this._cgiRoot, this._mmgisUrlRoot, this._util, this);
        statisticEventListener (this._interface, this._cgiRoot, this._handlers.statisticHandler, this._util);
    }

    MTEListener.prototype.appendTargetClickEventListener = function (targetDiv, resultBlock) {
        var self = this;
        $(targetDiv).click(function () {
            self._handlers.targetClickHandler(resultBlock, self._util, self._interface, self, self._mmgisUrlRoot);
        });
    }

    MTEListener.prototype.appendShareButtonEventListener = function (shareButton, shareInput) {
        var self = this;
        $(shareButton).click(function () {
            self._handlers.shareButtonHandler(shareInput);
        });
    }

    MTEListener.prototype.appendANLinkEventListener = function (anButton, anLink) {
        var self = this;
        $(anButton).click(function () {
            self._handlers.anLinkHandler(anLink);
        });
    }

    function searchEventListener (mteInterface, autoCompletion, searchHandler, enterHandler, cgiRoot, mgisUrlRoot, util, listener) {
        $(mteInterface._searchButton).click(function (){
            searchHandler(mteInterface, autoCompletion._list, cgiRoot, mgisUrlRoot, util, listener);
        });
        $(mteInterface._inputField).on("keypress", function (event){
            enterHandler(event, mteInterface);
        });
    }

    function statisticEventListener (mteInterface, cgiRoot, statisticHandler, util) {
        $(mteInterface._statisticsButton).click(function () {
            statisticHandler(mteInterface, cgiRoot, util);
        });
    }

    return MTEListener;
});