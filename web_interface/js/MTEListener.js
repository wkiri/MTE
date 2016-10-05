define([
    'MTEHandler'
], function (
    MTEHandler
){
    "use strict";

    var MTEListener = function (mteInterface, autoCompletion, cgiRoot) {
        this._handlers = new MTEHandler(this);
        this._interface = mteInterface;
        this._autoCompletion = autoCompletion;
        this._cgiRoot = cgiRoot;
    }

    MTEListener.prototype.initEventListeners = function () {
        searchEventListener(this._interface, this._autoCompletion, this._handlers.searchHandler,
            this._handlers.enterHandler, this._cgiRoot);
        statisticEventListener (this._interface, this._cgiRoot, this._handlers.statisticHandler);
    }

    MTEListener.prototype.appendTargetClickEventListener = function (targetDiv, resultBlock) {
        var self = this;
        $(targetDiv).click(function () {
            self._handlers.targetClickHandler(resultBlock);
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

    function searchEventListener (mteInterface, autoCompletion, searchHandler, enterHandler, cgiRoot) {
        $(mteInterface._searchButton).click(function (){
            searchHandler(mteInterface, autoCompletion._list, cgiRoot);
        });
        $(mteInterface._inputField).on("keypress", enterHandler);
    }

    function statisticEventListener (mteInterface, cgiRoot, statisticHandler) {
        $(mteInterface._statisticsButton).click(function () {
            statisticHandler(mteInterface, cgiRoot);
        });
    }

    return MTEListener;
});