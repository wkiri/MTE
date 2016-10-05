define([
    'Util',
    'Constants'
], function (
    Util,
    CONSTANTS
){
    "use strict";

    var MTEHandler = function (mteListener) {
        this._util = new Util();
        this._listener = mteListener;
    }

    MTEHandler.prototype.searchHandler = function (mteInterface, autoCompletionList, cgiRoot) {
        var self = this;
        var searchStr = $(mteInterface._inputField).val().toLowerCase();
        var targetMatches = this._util.getTargetMatches(autoCompletionList, searchStr);
        var componentMatches = this._util.getComponentMatches(autoCompletionList, searchStr);

        //remove all previous search results when perform a new search
        mteInterface.removeAllPreviousResults();

        //If there are no matches found in targets and components tables, then exist.
        if (targetMatches === 0 && componentMatches === 0) {
            mteInterface.setStatusLabel("Target not found");
            return;
        }

        $.ajax({
            url: cgiRoot + CONSTANTS.SERVER_GET_RESULTS_BY_SEARCHSTR,
            type: "post",
            dataType: "json",
            data: {
                searchStr: searchStr
            },
            success: function (returnedList) {
                var formattedList = self._util.getReformattedList(returnedList);
                if (formattedList.length === 0 && targetMatches !== 0) {
                    featchResultsWOProperties (searchStr, formattedList, self._util, mteInterface, self._listener);
                } else {
                    if (formattedList.length === 1) {
                        mteInterface.setStatusLabel("1 target found");
                    } else {
                        mteInterface.setStatusLabel(formattedList.length + " targets found");
                    }

                    mteInterface.displayResults(formattedList, self._listener, self._util);
                }
            }
        });
    }

    MTEHandler.prototype.enterHandler = function (event) {
        var self = this;
        if (event.which === 13) {
            $(self._interface._searchButton).focus();
            $(self._interface._searchButton).click();
        }
    }

    MTEHandler.prototype.targetClickHandler = function (resultBlock) {
        var displayList = this._util.getDisplayList(resultBlock);

        //case-insensitive sort (A-Z)
        displayList.element.sort(this._util.sortBy("component", true, function (str) {
            return str.trim().toLowerCase();
        }));
        displayList.mineral.sort(this._util.sortBy("component", true, function (str) {
            return str.trim().toLowerCase();
        }));
        displayList.material.sort(this._util.sortBy("component", true, function (str) {
            return str.trim().toLowerCase();
        }));
        displayList.feature.sort(this._util.sortBy("component", true, function (str) {
            return str.trim().toLowerCase();
        }));

        this._interface.buildSingleTargetPage(resultBlock, displayList, this._listener);
    }

    MTEHandler.prototype.shareButtonHandler = function (shareInput) {
        shareInput.select();
        try {
            document.execCommand("copy");
        } catch (err) {
            alert("Your browser doesn't support this functionality. Please copy the URL manually.");
        }
    }

    MTEHandler.prototype.anLinkHandler = function (anLink) {
        window.open(anLink);
    }

    MTEHandler.prototype.statisticHandler = function (mteInterface, cgiRoot) {
        var self = this;
        $.ajax({
            url: cgiRoot + CONSTANTS.SERVER_GET_STATISTIC,
            type: "post",
            dataType: "json",
            success: function (returnedDict) {
                var statisticList = self._util.getStatisticList(returnedDict);
                mteInterface.createColumnChart(statisticList);
            }
        });
    }

    function featchResultsWOProperties (searchStr, formattedList, util, mteInterface, mteListener) {
        $.ajax({
            url: "http://mte.jpl.nasa.gov/cgi/getResultsWOProperties.py",
            type: "post",
            dataType: "json",
            data: {
                searchStr: searchStr
            },
            success: function (returnedList) {
                util.addResultsToList(returnedList, formattedList);
                if (formattedList.length === 1) {
                    mteInterface.setStatusLabel("1 target found");
                } else {
                    mteInterface.setStatusLabel(formattedList.length + " targets found");
                }

                mteInterface.displayResults(formattedList, mteListener, util);
            }
        });
    }

    return MTEHandler;
});
