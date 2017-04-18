define([
    'Constants'
], function (
    CONSTANTS
){
    "use strict";

    var MTEHandler = function () {}

    MTEHandler.prototype.searchHandler = function (mteInterface, autoCompletionList, cgiRoot, mmgisUrlRoot, util, listener) {
        var searchStr = $(mteInterface._inputField).val().toLowerCase();
        var targetMatches = util.getTargetMatches(autoCompletionList, searchStr);
        var componentMatches = util.getComponentMatches(autoCompletionList, searchStr);

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
               var formattedList = util.getReformattedList(returnedList);
               if (formattedList.length === 0 && targetMatches !== 0) {
                   featchResultsWOProperties (cgiRoot, searchStr, formattedList, util, mteInterface, listener, mmgisUrlRoot);
               } else {
                   if (formattedList.length === 1) {
                       mteInterface.setStatusLabel("1 target found");
                   } else {
                       mteInterface.setStatusLabel(formattedList.length + " targets found");
                   }

                   mteInterface.displayResults(formattedList, listener, util, mmgisUrlRoot);
               }
           }
        });
    }

    MTEHandler.prototype.enterHandler = function (event, mteInterface) {
        if (event.which === 13) {
            $(mteInterface._searchButton).focus();
            $(mteInterface._searchButton).click();
        }
    }

    MTEHandler.prototype.targetClickHandler = function (resultBlock, util, mteInterface, mteListener, mmgisUrlRoot) {
        var displayList = util.getDisplayList(resultBlock);

        //case-insensitive sort (A-Z)
        displayList.element.sort(util.sortBy("component", true, function (str) {
            return str.trim().toLowerCase();
        }));
        displayList.mineral.sort(util.sortBy("component", true, function (str) {
            return str.trim().toLowerCase();
        }));
        displayList.material.sort(util.sortBy("component", true, function (str) {
            return str.trim().toLowerCase();
        }));
        displayList.feature.sort(util.sortBy("component", true, function (str) {
            return str.trim().toLowerCase();
        }));

        mteInterface.buildSingleTargetPage(resultBlock, displayList, mteListener, mmgisUrlRoot);
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

    MTEHandler.prototype.statisticHandler = function (mteInterface, cgiRoot, util) {
        $.ajax({
            url: cgiRoot + CONSTANTS.SERVER_GET_STATISTIC,
            type: "post",
            dataType: "json",
            success: function (returnedDict) {
                var statisticList = util.getStatisticList(returnedDict);
                mteInterface.createColumnChart(statisticList);
            }
        });
    }

    function featchResultsWOProperties (cgiRoot, searchStr, formattedList, util, mteInterface, mteListener, mmgisUrlRoot) {
        $.ajax({
            url: cgiRoot + CONSTANTS.SERVER_GET_RESULTS_WITHOUT_PROPERTIES,
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

                mteInterface.displayResults(formattedList, mteListener, util, mmgisUrlRoot);
            }
        });
    }

    return MTEHandler;
});
