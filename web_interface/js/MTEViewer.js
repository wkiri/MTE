define([

], function (

) {
    "use strict";

    var MTEViewer = function () {
        var url = location.href;
        dispatch(url, this);
    }

    function dispatch (url, mte) {
        if (url.indexOf("?") > -1) {
            singleTargetView(url, mte);
        } else {
            searchView(mte);
        }
    }

    //e.x. http://mte.jpl.nasa.gov?lookup=Windjana
    function singleTargetView (url, mte) {
        var index = url.indexOf("?");
        var partialUrl = url.substring(0, index);
        var parameter = url.substring(index + 1, url.length);
        window.history.pushState("", "", partialUrl);

        var parameterTokens = parameter.split("=");
        if (parameterTokens.length !== 2) {
            throw new Error("Invalid URL. Valid URL is in the form of http://server_name:port?lookup=target_name.");
        }
        var targetName = parameterTokens[1];

        searchView(mte);

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

    function searchView (mte) {
        mte._autoCompletionList = [];
        constructInterface ();
        customizeAutoCompletion();
        initTargetList(mte);
        initComponentList(mte);
        enableAutoCompletion(mte);
        enableSearchButton(mte);
        enableStatisticsButton(mte);
    }

    function constructInterface () {
        var mteContainer = document.getElementsByClassName("mte-container")[0];
        var mteLogo = document.createElement("div");
        var mteSearch = document.createElement("div");
        var mteResults = document.createElement("div");

        mteLogo.className = "mte-logo";
        mteSearch.className = "mte-search";
        mteResults.className = "mte-results";

        mteContainer.appendChild(mteLogo);
        mteContainer.appendChild(mteSearch);
        mteContainer.appendChild(mteResults);

        //logo panel
        mteLogo.appendChild(document.createTextNode("Mars Target Encyclopedia"));

        //search panel
        var mteSearchComponent = document.createElement("div");
        mteSearchComponent.className = "mte-search-component input-group col-lg-9";
        var inputField = document.createElement("input");
        inputField.type = "text";
        inputField.className = "form-control";
        inputField.id = "mteSearchInput";
        inputField.placeholder = "Enter target or component name";
        var buttonSpan = document.createElement("span");
        buttonSpan.className = "input-group-btn";
        var searchButton = document.createElement("button");
        searchButton.type = "button";
        searchButton.id = "searchButton";
        searchButton.className = "btn btn-info";
        var searchButtomImg = document.createElement("img");
        searchButtomImg.src = "images/search-icon.png";
        searchButtomImg.height = "15";
        var statisticsButton = document.createElement("button");
        statisticsButton.type = "button";
        statisticsButton.id = "statisticsButton";
        statisticsButton.className = "btn btn-info";
        $(statisticsButton).attr("data-toggle", "modal");
        $(statisticsButton).attr("data-target", "#statistics-results");
        var statisticsButtonImg = document.createElement("img");
        statisticsButtonImg.src = "images/statistics.png";
        statisticsButtonImg.height = "15";

        mteSearch.appendChild(mteSearchComponent);
        mteSearchComponent.appendChild(inputField);
        mteSearchComponent.appendChild(buttonSpan);
        buttonSpan.appendChild(searchButton);
        buttonSpan.appendChild(statisticsButton);
        searchButton.appendChild(searchButtomImg);
        statisticsButton.appendChild(statisticsButtonImg);

        //results panel
        var mteResultsStatus = document.createElement("div");
        mteResultsStatus.className = "mte-results-status";
        mteResultsStatus.id = "mteResultsStatus";
        var mteResultsDisplay = document.createElement("div");
        mteResultsDisplay.className = "mte-results-display";
        mteResultsDisplay.id = "mteResultsDisplay";

        mteResults.appendChild(mteResultsStatus);
        mteResults.appendChild(mteResultsDisplay);
    }

    function initTargetList (mte) {
        $.ajax({
            url: "http://mte.jpl.nasa.gov/cgi/getTargetsName.py",
            type: "post",
            dataType: "json",
            success: function (returnedList) {
                var results = returnedList.target_name;

                for (var i = 0; i < results.length; i++) {
                    if (isNameInList(results[i][0], mte._autoCompletionList)) {
                        continue;
                    }

                    mte._autoCompletionList.push({
                        label: results[i][0],
                        category: "Target"
                    });
                }
            }
        });
    }

    //load component names
    function initComponentList (mte) {
        $.ajax({
            url: "http://mte.jpl.nasa.gov/cgi/getComponentsNameAndLabel.py",
            type: "post",
            dataType: "json",
            success: function (returnedList) {
                var results = returnedList.results;

                for (var i = 0; i < results.length; i++) {
                    if (isNameInList(results[i][0], mte._autoCompletionList)) {
                        continue;
                    }

                    mte._autoCompletionList.push({
                        label: results[i][0],
                        category: results[i][1]
                    });
                }
            }
        });
    }

    function isNameInList(targetName, list) {
        var flag = false;

        for (var i = 0; i < list.length; i++) {
            if (list[i].label === targetName) {
                flag = true;
                break;
            }
        }

        return flag;
    }

    //enable target name auto-completion
    function enableAutoCompletion (mte) {
        $('#mteSearchInput').catcomplete({
            delay: 0,
            source: mte._autoCompletionList
        });
    }

    //enable auto completion with categories.
    //exData = [{label: "aaa", category: "target"},
    //          {label: "bbb", category: "Element"}]
    function customizeAutoCompletion () {
        $.widget( "custom.catcomplete", $.ui.autocomplete, {
            _create: function() {
                this._super();
                this.widget().menu( "option", "items", "> :not(.ui-autocomplete-category)" );
            },
            _renderMenu: function( ul, items ) {
                var that = this,
                    currentCategory = "";
                $.each( items, function( index, item ) {
                    var li;
                    if ( item.category != currentCategory ) {
                        ul.append( "<li class='ui-autocomplete-category'>" + item.category + "</li>" );
                        currentCategory = item.category;
                    }
                    li = that._renderItemData( ul, item );
                    if ( item.category ) {
                        li.attr( "aria-label", item.category + " : " + item.label );
                    }
                });
            }
        });
    }

    //function updateUrl (parameter, value) {
    //    var currentUrl = location.href;
    //    if (currentUrl.indexOf("?") <= -1) {
    //        currentUrl = currentUrl + "?";
    //    }
    //
    //    if (currentUrl.indexOf(parameter) > -1) {
    //        var startIndex, endIndex;
    //        var urlTokens = currentUrl.split("=");
    //
    //    } else {
    //        if (currentUrl.substring(currentUrl.length - 1, currentUrl.length) === "?") {
    //            currentUrl = currentUrl + parameter + "=" + value;
    //        } else {
    //            currentUrl = currentUrl + "&" + parameter + "=" + value;
    //        }
    //
    //        window.history.pushState("", "", currentUrl);
    //    }
    //}

    function enableSearchButton (mte) {
        $("#searchButton").click(searchHandler);
        $("#mteSearchInput").on("keypress", function (event) {
            if (event. which === 13) {
                $("#searchButton").focus();
                $("#searchButton").click();
            }
        });

        function searchHandler () {
            var searchString = $("#mteSearchInput").val().toLowerCase();
            var resultsStatusPanel = document.getElementById("mteResultsStatus");
            var resultsDisplayPanel = document.getElementById("mteResultsDisplay");
            var targetMatchesList = [];
            var targetMatches = 0;
            var componentMatches = 0;

            for (var i = 0; i < mte._autoCompletionList.length; i++) {
                if (mte._autoCompletionList[i].label.toLowerCase().indexOf(searchString) > -1) {
                    if (mte._autoCompletionList[i].category === "Target") {
                        targetMatches++;
                        targetMatchesList.push(mte._autoCompletionList[i].label);
                    } else {
                        componentMatches++;
                    }
                }
            }

            //no results found
            if (targetMatches === 0 && componentMatches === 0) {
                resultsStatusPanel.innerHTML = "target not found.";

                //remove everything in div
                var resultsDiv = document.getElementById("mteResultsDisplay");
                while (resultsDiv.hasChildNodes()) {
                    resultsDiv.removeChild(resultsDiv.lastChild);
                }

                return;
            }

            $.ajax({
                url: "http://mte.jpl.nasa.gov/cgi/getResultsBySearchStr.py",
                type: "post",
                dataType: "json",
                data: {
                    searchStr: searchString
                },
                success: function (returnedList) {
                    var formattedList = [];
                    for (var i = 0; i < returnedList.results.length; i++) {
                        var targetName = returnedList.results[i][0];
                        var targetId = returnedList.results[i][1];
                        var targetFirstSol = returnedList.results[i][2];
                        if (isNameInList(targetName, formattedList)) {
                            for (var j = 0; j < formattedList.length; j++) {
                                if (formattedList[j].label === targetName) {
                                    formattedList[j].associates.push({
                                        component: returnedList.results[i][3],
                                        authors: returnedList.results[i][4],
                                        publication: returnedList.results[i][5],
                                        excerpt: returnedList.results[i][6],
                                        docUrl: returnedList.results[i][7]
                                    });
                                }
                            }
                        } else {
                            formattedList.push({
                                label: targetName,
                                id: targetId,
                                firstSol: targetFirstSol,
                                associates: [{
                                    component: returnedList.results[i][3],
                                    authors: returnedList.results[i][4],
                                    publication: returnedList.results[i][5],
                                    excerpt: returnedList.results[i][6],
                                    docUrl: returnedList.results[i][7]
                                }]
                            });
                        }
                    }

                    if (formattedList.length === 0 && targetMatchesList !== 0) {
                        //TODO break into more detailed cases.
                        $.ajax({
                            url: "http://mte.jpl.nasa.gov/cgi/getResultsWOProperties.py",
                            type: "post",
                            dataType: "json",
                            data: {
                                searchStr: searchString
                            },
                            success: function (returnedList) {
                                for (var i = 0; i < returnedList.results.length; i++) {
                                    var targetName = returnedList.results[i][0];
                                    var targetId = returnedList.results[i][1];
                                    var targetFirstSol = returnedList.results[i][2];
                                    formattedList.push({
                                        label: targetName,
                                        id: targetId,
                                        firstSol: targetFirstSol,
                                        associates: [{
                                            component: "undefined",
                                            authors: "undefined",
                                            publication: "undefined",
                                            excerpt: "undefined",
                                            docUrl: "undefined"
                                        }]
                                    });
                                }

                                resultsStatusPanel.innerHTML = formattedList.length + " targets found."
                                displayResults(formattedList, mte);
                            }
                        });
                    } else {
                        resultsStatusPanel.innerHTML = formattedList.length + " targets found."
                        displayResults(formattedList, mte);
                    }
                }
            });
        }
    }

    function displayResults (formattedList, mte) {
        console.log(formattedList);
        var resultsDiv = document.getElementById("mteResultsDisplay");

        //remove everything in div
        while (resultsDiv.hasChildNodes()) {
            resultsDiv.removeChild(resultsDiv.lastChild);
        }

        for (var i = 0; i < formattedList.length; i++) {
            //unit result container
            var resultBlock = document.createElement("div");
            resultBlock.className = "mte-results-display-block"
            resultsDiv.appendChild(resultBlock);

            //thumbnail image
            //TODO thumbnail image URLs are fake now!!!!
            var thumbnailDiv = document.createElement("div");
            var thumbnailImg = document.createElement("img");
            thumbnailDiv.className = "mte-results-display-block-img";
            $(thumbnailDiv).attr("data-toggle", "modal");
            $(thumbnailDiv).attr("data-target", "#singleTargetDiv");
            thumbnailImg.src = "https://an.rsl.wustl.edu/msl/mslbrowser/sqlImageHandler.ashx?t=th&id=" + formattedList[i].id;
            thumbnailDiv.appendChild(thumbnailImg);
            resultBlock.appendChild(thumbnailDiv);
            resultBlock.thumbnailUrl = "https://an.rsl.wustl.edu/msl/mslbrowser/sqlImageHandler.ashx?t=th&id=" + formattedList[i].id;

            //text div
            var textDiv = document.createElement("div");
            textDiv.className = "mte-results-display-block-text";
            resultBlock.appendChild(textDiv);

            //target name
            var targetDiv = document.createElement("div");
            targetDiv.className = "mte-results-display-block-text-target";
            targetDiv.id = formattedList[i].label;
            targetDiv.appendChild(document.createTextNode(formattedList[i].label));
            textDiv.appendChild(targetDiv);
            $(targetDiv).attr("data-toggle", "modal");
            $(targetDiv).attr("data-target", "#singleTargetDiv");
            resultBlock.targetName = formattedList[i].label;
            resultBlock.firstSol = formattedList[i].firstSol;

            //properties
            var propertyDiv = document.createElement("div");
            propertyDiv.className = "mte-results-display-block-text-property";
            if (formattedList[i].associates.length === 1) {
                if (formattedList[i].associates[0].component === "undefined") {
                    propertyDiv.appendChild(document.createTextNode("0 property"));
                } else {
                    propertyDiv.appendChild(document.createTextNode(formattedList[i].associates.length + " property"));
                }
            } else {
                propertyDiv.appendChild(document.createTextNode(formattedList[i].associates.length + " properties"));
            }
            textDiv.appendChild(propertyDiv);
            resultBlock.associates = formattedList[i].associates;

            //publications
            var nonDuplicatePublicationList = getNonDuplicatePublication(formattedList[i].associates);
            var publicationDiv = document.createElement("div");
            publicationDiv.className = "mte-results-display-block-text-publication";
            if (nonDuplicatePublicationList.length === 1) {
                if (formattedList[i].associates[0].component === "undefined") {
                    publicationDiv.appendChild(document.createTextNode("0 publication"));
                } else {
                    publicationDiv.appendChild(document.createTextNode(nonDuplicatePublicationList.length + " publication"));
                }
            } else {
                publicationDiv.appendChild(document.createTextNode(nonDuplicatePublicationList.length + " publications"));
            }
            textDiv.appendChild(publicationDiv);

            //layout
            var msnry = new Masonry(resultsDiv, {
                itemSelector: ".mte-results-display-block",
                columnWidth: 244,
                gutter: 10
            });

            //attach target name click event
            targetNameClickHandler(targetDiv, resultBlock);
            targetNameClickHandler(thumbnailDiv, resultBlock);
        }
    }

    function targetNameClickHandler (targetDiv, resultBlock) {
        $(targetDiv).click(function () {
            var targetName = resultBlock.targetName;
            var thumbnailUrl = resultBlock.thumbnailUrl;
            var targetAssociates = resultBlock.associates;
            var divHeader = document.getElementById("singleTargetDivHeader");
            var divDisplay = document.getElementById("singleTargetDivDisplay");

            //remove pervious content
            var thumbnail = document.getElementById("targetThumbnail")
            if (thumbnail !== null && thumbnail !== undefined) {
                divHeader.removeChild(thumbnail);
            }

            var h4 = document.getElementById("targetTitle");
            if (h4 !== null && h4 !== undefined) {
                divHeader.removeChild(h4);
            }

            var shareButton = document.getElementById("shareButton");
            if (shareButton !== null && shareButton !== undefined) {
                divHeader.removeChild(shareButton);
            }

            while (divDisplay.hasChildNodes()) {
                divDisplay.removeChild(divDisplay.lastChild);
            }

            //thumbnail
            thumbnail = document.createElement("img");
            thumbnail.id = "targetThumbnail";
            thumbnail.src = thumbnailUrl;
            divHeader.appendChild(thumbnail);

            //target name
            h4 = document.createElement("h4");
            h4.id = "targetTitle";
            h4.appendChild(document.createTextNode(targetName));
            divHeader.appendChild(h4);

            //share button
            shareButton = document.createElement("input");
            shareButton.type = "button";
            shareButton.className = "btn btn-info btn-sm";
            shareButton.id = "shareButton";
            shareButton.value = "Share Target " + targetName;
            divHeader.appendChild(shareButton);

            $(shareButton).click(function () {
                var url = location.href;
                url = url + "?lookup=" + targetName;
                var promptStr = "Copy to clipboard: Ctrl+C, Enter";
                window.prompt(promptStr, url);
            });

            //root list
            var rootUl = document.createElement("ul");
            //rootUl.className = "mte-root-ul";
            divDisplay.appendChild(rootUl);

            //target first sol
            var firstSolLi = document.createElement("li");
            firstSolLi.className = "mte-title-li";
            firstSolLi.appendChild(document.createTextNode("First defined on SOL: " + resultBlock.firstSol));
            rootUl.appendChild(firstSolLi);

            //properties
            var propertyLi = document.createElement("li");
            propertyLi.className = "mte-title-li";
            var propertyContentUl = document.createElement("ul");
            propertyLi.appendChild(document.createTextNode("Properties: "));
            propertyLi.appendChild(propertyContentUl);
            rootUl.appendChild(propertyLi);

            //case-insensitive sort by component_name (A-Z)
            resultBlock.associates.sort(sortBy("component", true, function (str) {
                return str.trim().toLowerCase();
            }));

            for (var i = 0; i < resultBlock.associates.length; i++) {
                var li = document.createElement('li');
                li.className = "mte-content-li";
                var componentStr = resultBlock.associates[i].component;
                var excerptStr = '"' + resultBlock.associates[i].excerpt + '"';
                var authorsStr = resultBlock.associates[i].authors;
                var publicationStr = ' "' + resultBlock.associates[i].publication + '"';
                var docUrl = resultBlock.associates[i].docUrl;

                //TODO temp solution for authors string being too long
                if (authorsStr.length > 20) {
                    authorsStr = authorsStr.substring(0, 20) + ' et al.';
                }

                if (authorsStr.length === 0) {
                    authorsStr = "Unknow";
                }
                authorsStr = "[" + authorsStr + "]";

                var componentTextNode = document.createElement("b");
                componentTextNode.innerHTML = componentStr;
                var excerptTextNode = document.createTextNode(excerptStr);
                var authorsTextNode = document.createTextNode(authorsStr);
                var publicationLink = document.createElement("a");
                var publicationTextNode = document.createTextNode(publicationStr);
                publicationLink.href = docUrl;
                publicationLink.target = "_blank";
                publicationLink.appendChild(publicationTextNode);

                li.appendChild(componentTextNode);
                li.appendChild(document.createElement("br"));
                li.appendChild(excerptTextNode);
                li.appendChild(document.createElement("br"));
                li.appendChild(authorsTextNode);
                li.appendChild(publicationLink);
                propertyContentUl.appendChild(li);
            }

            //publications
            //var publicationLi = document.createElement("li");
            //publicationLi.className = "mte-title-li";
            //var publicationContentUl = document.createElement("ul");
            //publicationLi.appendChild(document.createTextNode("Publications:"));
            //publicationLi.appendChild(publicationContentUl);
            //rootUl.appendChild(publicationLi);
            ////case-insensitive sort by author name (A-Z)
            //resultBlock.associates.sort(sortBy("authors", true, function (str) {
            //    return str.trim().toLowerCase();
            //}));
            //
            //for (var i = 0; i < resultBlock.associates.length; i++) {
            //    var li = document.createElement("li");
            //    li.className = "mte-content-li";
            //    var publicationTitleStr = resultBlock.associates[i].publication;
            //    var authorsStr = resultBlock.associates[i].authors;
            //
            //    //TODO temp solution for authors string being too long
            //    if (authorsStr.length > 20) {
            //        authorsStr = authorsStr.substring(0, 20) + ' et al.';
            //    }
            //
            //    if (authorsStr.length === 0) {
            //        authorsStr = "unknown author";
            //    }
            //
            //    if (publicationTitleStr.length === 0) {
            //        publicationTitleStr = "unknow publication title";
            //    }
            //
            //    var publicationStr = authorsStr + ', "' + publicationTitleStr + '"';
            //    var perviousLi = publicationContentUl.lastChild;
            //
            //    if (perviousLi !== null && $(perviousLi.innerHTML).text() === publicationStr) {
            //        continue;
            //    }
            //
            //    var publicationLink = document.createElement("a");
            //    publicationLink.appendChild(document.createTextNode(publicationStr));
            //    publicationLink.href = resultBlock.associates[i].docUrl;
            //    publicationLink.target = "_blank";
            //    li.appendChild(publicationLink);
            //    publicationContentUl.appendChild(li);
            //}
        });
    }

    function sortBy (field, reverse, primer) {
        var key = function (x) {return primer ? primer(x[field]) : x[field]};

        return function (a,b) {
            var A = key(a), B = key(b);
            return ( (A < B) ? -1 : ((A > B) ? 1 : 0) ) * [-1,1][+!!reverse];
        }
    }

    function getNonDuplicatePublication (associatesList) {
        var nonDuplicatePublicationList = [];

        for (var i = 0; i < associatesList.length; i++) {
            var publicationTitle = associatesList[i].publication;

            if (nonDuplicatePublicationList.indexOf(publicationTitle) <= -1) {
                nonDuplicatePublicationList.push(publicationTitle);
            }
        }

        return nonDuplicatePublicationList;
    }

    function enableStatisticsButton(mte) {
        $('#statisticsButton').click(function () {
            statisticsHandler();
        });

        function statisticsHandler () {
            $.ajax({
                url: "http://mte.jpl.nasa.gov/cgi/getStatistics.py",
                type: "post",
                dataType: "json",
                success: function (returnedDict) {
                    var data = [];
                    var document_count = returnedDict.document_count[0][0];
                    var target_count = returnedDict.target_count[0][0];
                    var event_count = returnedDict.event_count[0][0];
                    var element_count = returnedDict.element_count[0][0];
                    var feature_count = returnedDict.feature_count[0][0];
                    var material_count = returnedDict.material_count[0][0];
                    var mineral_count = returnedDict.mineral_count[0][0];

                    data.push(document_count);
                    data.push(target_count);
                    data.push(event_count);
                    data.push(element_count);
                    data.push(feature_count);
                    data.push(material_count);
                    data.push(mineral_count);


                    createColumnChart(data)
                }
            });
        }

        function createColumnChart (data) {
            $('#statisticsDisplay').highcharts({
                chart: {
                    type: 'column'
                },
                title: {
                    text: ''
                },
                xAxis: {
                    categories: ['Documents', 'Targets', 'Relations', 'Elements', 'Features', 'Materials', 'Minerals'],
                },
                yAxis: {
                    min: 0,
                    title: {
                        text: 'Total Number'
                    }
                },
                credits: {
                    enabled: false
                },
                series: [{
                    name: 'Number',
                    data: data
                }]
            });
        }
    }

    return MTEViewer;
});