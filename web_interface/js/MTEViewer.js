define([

], function (

) {
    "use strict";

    var MTEViewer = function () {
        this._autoCompletionList = [];

        customizeAutoCompletion();
        initAutoCompletionList(this);
        //initComponentList(this);
        enableAutoCompletion(this);
        enableSearchButton(this);
        enableStatisticsButton(this);
    }

    function initAutoCompletionList (mte) {
        $.ajax({
            url: "http://mte.jpl.nasa.gov/cgi/getAutoCompletionList.py",
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

    //load component names
    //function initComponentList (mte) {
    //    $.ajax({
    //        url: "http://mte.jpl.nasa.gov/cgi/getComponentsNameAndLabel.py",
    //        type: "post",
    //        dataType: "json",
    //        success: function (returnedList) {
    //            var results = returnedList.results;
    //
    //            for (var i = 0; i < results.length; i++) {
    //                if (isNameInList(results[i][0], mte._autoCompletionList)) {
    //                    continue;
    //                }
    //
    //                mte._autoCompletionList.push({
    //                    label: results[i][0],
    //                    category: results[i][1]
    //                });
    //            }
    //        }
    //    });
    //}

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

    function enableSearchButton (mte) {
        $("#searchButton").click(searchHandler);
        $("#mteSearchInput").on("keypress", function (event) {
            if (event. which === 13) {
                $("#searchButton").focus();
                $("#searchButton").click();
            }
        });

        function searchHandler () {
            console.log(location.href);
            var searchString = $("#mteSearchInput").val().toLowerCase();
            var resultsStatusPanel = document.getElementById("mteResultsStatus");
            var resultsDisplayPanel = document.getElementById("mteResultsDisplay");
            var targetMatches = 0;
            var componentMatches = 0;

            for (var i = 0; i < mte._autoCompletionList.length; i++) {
                if (mte._autoCompletionList[i].label.toLowerCase().indexOf(searchString) > -1) {
                    if (mte._autoCompletionList[i].category === "Target") {
                        targetMatches++;
                    } else {
                        componentMatches++;
                    }
                }
            }

            //no results found
            if (targetMatches === 0 && componentMatches === 0) {
                resultsStatusPanel.innerHTML = "Nothing found.";
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
                                        excerpt: returnedList.results[i][6]
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
                                    excerpt: returnedList.results[i][6]
                                }]
                            });
                        }
                    }

                    resultsStatusPanel.innerHTML = formattedList.length + " targets are found."
                    displayResults(formattedList, mte);

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
            targetDiv.appendChild(document.createTextNode(formattedList[i].label));
            textDiv.appendChild(targetDiv);
            $(targetDiv).attr("data-toggle", "modal");
            $(targetDiv).attr("data-target", "#singleTargetDiv");
            resultBlock.targetName = formattedList[i].label;
            resultBlock.firstSol = formattedList[i].firstSol;

            //properties
            var propertyDiv = document.createElement("div");
            propertyDiv.className = "mte-results-display-block-text-property";
            propertyDiv.appendChild(document.createTextNode(formattedList[i].associates.length + " property"));
            textDiv.appendChild(propertyDiv);
            resultBlock.associates = formattedList[i].associates;

            //publications
            var nonDuplicatePublicationList = getNonDuplicatePublication(formattedList[i].associates);
            var publicationDiv = document.createElement("div");
            publicationDiv.className = "mte-results-display-block-text-publication";
            publicationDiv.appendChild(document.createTextNode(nonDuplicatePublicationList.length + " publication"));
            textDiv.appendChild(publicationDiv);

            //layout
            var msnry = new Masonry(resultsDiv, {
                itemSelector: ".mte-results-display-block",
                columnWidth: 244,
                gutter: 10
            });

            //attach target name click event
            targetNameClickHandler(targetDiv, resultBlock);
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

            //root list
            var rootUl = document.createElement("ul");
            //rootUl.className = "mte-root-ul";
            divDisplay.appendChild(rootUl);

            //target first sol
            var firstSolLi = document.createElement("li");
            firstSolLi.className = "mte-title-li";
            firstSolLi.appendChild(document.createTextNode("First observed on SOL: " + resultBlock.firstSol));
            rootUl.appendChild(firstSolLi);

            //properties
            var propertyLi = document.createElement("li");
            propertyLi.className = "mte-title-li";
            var propertyContentUl = document.createElement("ul");
            propertyLi.appendChild(document.createTextNode("Properties: "));
            propertyLi.appendChild(propertyContentUl);
            rootUl.appendChild(propertyLi);

            for (var i = 0; i < resultBlock.associates.length; i++) {
                var li = document.createElement('li');
                li.className = "mte-content-li";
                var componentStr = resultBlock.associates[i].component;
                var excerpt = resultBlock.associates[i].excerpt;
                var authorsStr = resultBlock.associates[i].authors;

                //TODO temp solution for authors string being too long
                if (authorsStr.length > 20) {
                    authorsStr = authorsStr.substring(0, 20) + ' et al.';
                }

                if (authorsStr.length === 0) {
                    authorsStr = "unknown author";
                }

                var propertyStr = componentStr + " [" + authorsStr + "] " + excerpt;
                li.appendChild(document.createTextNode(propertyStr));
                propertyContentUl.appendChild(li);
            }

            //publications
            var publicationLi = document.createElement("li");
            publicationLi.className = "mte-title-li";
            var publicationContentUl = document.createElement("ul");
            publicationLi.appendChild(document.createTextNode("Publications:"));
            publicationLi.appendChild(publicationContentUl);
            rootUl.appendChild(publicationLi);

            for (var i = 0; i < resultBlock.associates.length; i++) {
                var li = document.createElement("li");
                li.className = "mte-content-li";
                var publicationTitleStr = resultBlock.associates[i].publication;
                var authorsStr = resultBlock.associates[i].authors;

                //TODO temp solution for authors string being too long
                if (authorsStr.length > 20) {
                    authorsStr = authorsStr.substring(0, 20) + ' et al.';
                }

                if (authorsStr.length === 0) {
                    authorsStr = "unknown author";
                }

                if (publicationTitleStr.length === 0) {
                    publicationTitleStr = "unknow publication title";
                }

                var publicationStr = authorsStr + ', "' + publicationTitleStr + '"';
                var perviousLi = publicationContentUl.lastChild;
                if (perviousLi !== null && perviousLi.innerHTML === publicationStr) {
                    continue;
                }

                li.appendChild(document.createTextNode(publicationStr));
                publicationContentUl.appendChild(li);
            }
        });
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
                    console.log(returnedDict);

                    var data = [];
                    var document_count = returnedDict.document_count[0][0];
                    var target_count = returnedDict.target_count[0][0];
                    var element_count = returnedDict.element_count[0][0];
                    var feature_count = returnedDict.feature_count[0][0];
                    var material_count = returnedDict.material_count[0][0];
                    var mineral_count = returnedDict.mineral_count[0][0];
                    var event_count = returnedDict.event_count[0][0];

                    data.push(document_count);
                    data.push(target_count);
                    data.push(element_count);
                    data.push(feature_count);
                    data.push(material_count);
                    data.push(mineral_count);
                    data.push(event_count);

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
                    categories: ['Document', 'Target', 'Element', 'Feature', 'Material', 'Mineral' , 'Event'],
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