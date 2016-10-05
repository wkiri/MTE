define([
    './Constants'
], function (
    CONSTANTS
) {
    "use strict";

    var Dispatcher = function (url) {
        this._url = url;
    }

    Dispatcher.prototype.getDispViewStr = function () {
        if (this._url.indexOf("?") > -1) {
            return CONSTANTS.LOOKUP_VIEW;
        } else {
            return CONSTANTS.NORMAL_VIEW;
        }
    }

    Dispatcher.prototype.getPartialURL = function () {
        var index = getURLSplitterIndex(this._url);
        return url.substring(0, index);
    }

    Dispatcher.prototype.getParameterTargetName = function () {
        var index = getURLSplitterIndex(this._url);
        var parameterStr = this._url.substring(index + 1, this._url.length);
        var parameterTokens = parameterStr.split("=");

        if (parameterTokens.length !== 2) {
            throw new Error("Invalid URL. Valid URL is in the form of http://hostname:port?lookup=target_name.");
        }

        return parameterTokens[1];
    }

    function getURLSplitterIndex (url) {
        return url.indexOf("?");
    }

    return Dispatcher;
})