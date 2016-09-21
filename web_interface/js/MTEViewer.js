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
        var mteSubtitle = document.createElement("div");
        var mteSearch = document.createElement("div");
        var mteResults = document.createElement("div");

        mteLogo.className = "mte-logo";
        mteSubtitle.className = "mte-subtitle";
        mteSearch.className = "mte-search";
        mteResults.className = "mte-results";

        mteContainer.appendChild(mteLogo);
        mteContainer.appendChild(mteSubtitle);
        mteContainer.appendChild(mteSearch);
        mteContainer.appendChild(mteResults);

        //logo panel
        mteLogo.appendChild(document.createTextNode("Mars Target Encyclopedia"));

        //subtitle panel
        var subtitle = "Compositional information from publications about MSL ChemCam surface targets";
        var holdings = "Publications currently indexed: abstracts from LPSC 2015 and 2016";
        mteSubtitle.appendChild(document.createTextNode(subtitle));
        mteSubtitle.appendChild(document.createElement("br"));
        mteSubtitle.appendChild(document.createTextNode(holdings));

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
                    if (isNameInList(results[i][0], mte._autoCompletionList, "label")) {
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
                    if (isNameInList(results[i][0], mte._autoCompletionList, "label")) {
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

    function isNameInList(targetName, list, identity) {
        var flag = false;

        for (var i = 0; i < list.length; i++) {
            if (list[i][identity] === targetName) {
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
            var searchString = $("#mteSearchInput").val().toLowerCase();
            var resultsStatusPanel = document.getElementById("mteResultsStatus");
            var resultsDisplayPanel = document.getElementById("mteResultsDisplay");
            var targetMatchesList = [];
            var targetMatches = 0;
            var componentMatches = 0;

            for (var i = 0; i < mte._autoCompletionList.length; i++) {
                if (mte._autoCompletionList[i].label.toLowerCase() === searchString) {
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
                resultsStatusPanel.innerHTML = "Target not found.";

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
                        if (isNameInList(targetName, formattedList, "label")) {
                            for (var j = 0; j < formattedList.length; j++) {
                                if (formattedList[j].label === targetName) {
                                    formattedList[j].associates.push({
                                        component: returnedList.results[i][3],
                                        componentLabel: returnedList.results[i][4],
                                        primaryAuthor: returnedList.results[i][5],
                                        publication: returnedList.results[i][6],
                                        excerpt: returnedList.results[i][7],
                                        year: returnedList.results[i][8],
                                        venue: returnedList.results[i][9],
                                        docUrl: returnedList.results[i][10]
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
                                    componentLabel: returnedList.results[i][4],
                                    primaryAuthor: returnedList.results[i][5],
                                    publication: returnedList.results[i][6],
                                    excerpt: returnedList.results[i][7],
                                    year: returnedList.results[i][8],
                                    venue: returnedList.results[i][9],
                                    docUrl: returnedList.results[i][10]
                                }]
                            });
                        }
                    }

                    if (formattedList.length === 0 && targetMatchesList !== 0) {
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
                                            componentLabel: "undefined",
                                            primaryAuthor: "undefined",
                                            publication: "undefined",
                                            excerpt: "undefined",
                                            year: "undefined",
                                            venue: "undefined",
                                            docUrl: "undefined"
                                        }]
                                    });
                                }

                                if (formattedList.length === 1) {
                                    resultsStatusPanel.innerHTML = "1 target found."
                                } else {
                                    resultsStatusPanel.innerHTML = formattedList.length + " targets found."
                                }
                                displayResults(formattedList, mte);
                            }
                        });
                    } else {
                        if (formattedList.length === 1) {
                            resultsStatusPanel.innerHTML = "1 target found."
                        } else {
                            resultsStatusPanel.innerHTML = formattedList.length + " targets found."
                        }
                        displayResults(formattedList, mte);
                    }
                }
            });
        }
    }

    function displayResults (formattedList, mte) {
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
            var thumbnailDiv = document.createElement("div");
            var thumbnailImg = document.createElement("img");
            thumbnailDiv.className = "mte-results-display-block-img";
            $(thumbnailDiv).attr("data-toggle", "modal");
            $(thumbnailDiv).attr("data-target", "#singleTargetDiv");
            if (formattedList[i].id !== undefined && formattedList[i].id !== "None") {
                thumbnailImg.src = "https://an.rsl.wustl.edu/msl/mslbrowser/sqlImageHandler.ashx?t=th&id=" + formattedList[i].id;
            } else {
                thumbnailImg.src = "images/empty_placeholder.png";
            }
            thumbnailDiv.appendChild(thumbnailImg);
            resultBlock.appendChild(thumbnailDiv);
            if (formattedList[i].id !== undefined && formattedList[i].id !== "None") {
                resultBlock.thumbnailUrl = "https://an.rsl.wustl.edu/msl/mslbrowser/sqlImageHandler.ashx?t=th&id=" + formattedList[i].id;
                resultBlock.anLink = "https://an.rsl.wustl.edu/msl/mslBrowser/an3.aspx?it=G1&ii=" + formattedList[i].id;
            } else {
                resultBlock.thumbnailUrl = "images/empty_placeholder.png";
            }


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
            targetClickHandler(targetDiv, resultBlock);
            targetClickHandler(thumbnailDiv, resultBlock);
        }
    }

    function targetClickHandler (targetDiv, resultBlock) {
        $(targetDiv).click(function () {
            var targetName = resultBlock.targetName;
            var thumbnailUrl = resultBlock.thumbnailUrl;
            var anLink = resultBlock.anLink;
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

            var shareDiv = document.getElementById("shareDiv");
            if (shareDiv !== null && shareDiv !== undefined) {
                divHeader.removeChild(shareDiv);
            }

            var anButton = document.getElementById("anButton");
            if (anButton !== null && anButton !== undefined) {
                divHeader.removeChild(anButton);
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
            var url = location.href;
            url = url + "?lookup=" + targetName;
            shareDiv = document.createElement("div");
            shareDiv.className = "input-group input-group-sm";
            shareDiv.id = "shareDiv";
            var shareInput = document.createElement("input");
            shareInput.type = "text";
            shareInput.className = "form-control";
            shareInput.value =url;
            shareInput.readOnly = "readonly";
            var shareSpan = document.createElement("span");
            shareSpan.className = "input-group-btn";
            var shareButton = document.createElement("button");
            shareButton.type = "button";
            shareButton.className = "btn btn-info btn-sm";
            $(shareButton).text("Copy to clipboard");
            shareDiv.appendChild(shareInput);
            shareDiv.appendChild(shareSpan);
            shareSpan.appendChild(shareButton);
            divHeader.appendChild(shareDiv);
            $(shareButton).click(function () {
                shareInput.select();
                try {
                    document.execCommand("copy");
                } catch (err) {
                    alert("Your browser doesn't support this functionality. Please copy the URL manually.");
                }
            });

            //anButton
            if (anLink !== undefined && anLink.length > 0) {
                anButton = document.createElement("input");
                anButton.type = "button";
                anButton.className = "btn btn-info btn-sm";
                anButton.id = "anButton";
                anButton.value = "Go to MSL Analyst's Notebook"
                divHeader.appendChild(anButton);
                $(anButton).click(function () {
                    window.open(anLink);
                });
            }

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

            var displayList = {
                element: [],
                mineral: [],
                material: [],
                feature: []
            }

            for (var i = 0; i < resultBlock.associates.length; i++) {
                var component = resultBlock.associates[i].component;
                var componentLabel = resultBlock.associates[i].componentLabel.toLocaleLowerCase();
                if (isNameInList(component, displayList[componentLabel], "component")) {
                    for (var j = 0; j < displayList[componentLabel].length; j++) {
                        if (displayList[componentLabel][j].component === component) {
                            displayList[componentLabel][j].content.push({
                                docUrl: resultBlock.associates[i].docUrl,
                                excerpt: resultBlock.associates[i].excerpt,
                                primaryAuthor: resultBlock.associates[i].primaryAuthor,
                                publication: resultBlock.associates[i].publication,
                                venue: resultBlock.associates[i].venue,
                                year: resultBlock.associates[i].year
                            });
                        }
                    }
                } else {
                    displayList[componentLabel].push({
                        component: component,
                        content: [{
                            docUrl: resultBlock.associates[i].docUrl,
                            excerpt: resultBlock.associates[i].excerpt,
                            primaryAuthor: resultBlock.associates[i].primaryAuthor,
                            publication: resultBlock.associates[i].publication,
                            venue: resultBlock.associates[i].venue,
                            year: resultBlock.associates[i].year
                        }]
                    });
                }
            }

            //case-insensitive sort (A-Z)
            displayList.element.sort(sortBy("component", true, function (str) {
                return str.trim().toLowerCase();
            }));
            displayList.mineral.sort(sortBy("component", true, function (str) {
                return str.trim().toLowerCase();
            }));
            displayList.material.sort(sortBy("component", true, function (str) {
                return str.trim().toLowerCase();
            }));
            displayList.feature.sort(sortBy("component", true, function (str) {
                return str.trim().toLowerCase();
            }));

            if (displayList.element.length > 0) {
                var elementLi = document.createElement("li");
                var elementUl = document.createElement("ul");
                elementLi.className = "mte-content-li-root";
                elementLi.appendChild(document.createTextNode("Element: "));
                elementLi.appendChild(elementUl);
                elementLi.appendChild(document.createElement("hr"));
                propertyContentUl.appendChild(elementLi);
                for (var i = 0; i < displayList.element.length; i++) {
                    var elementName = displayList.element[i].component;
                    var elementContent = displayList.element[i].content;
                    var elementNameLi = document.createElement("li");
                    var elementNameB = document.createElement("b");
                    elementNameB.innerHTML = elementName;
                    var elementContentOl = document.createElement("ol");
                    elementNameLi.className = "mte-content-li";
                    elementNameLi.appendChild(elementNameB);
                    elementNameLi.appendChild(elementContentOl);
                    elementUl.appendChild(elementNameLi);

                    for (var j = 0; j < elementContent.length; j++) {
                        var li = document.createElement("li");
                        li.className = "mte-content-li-property";
                        elementContentOl.appendChild(li);

                        var excerpt = '"' + elementContent[j].excerpt + '"';
                        var author = elementContent[j].primaryAuthor + " et al. ";
                        var year = "(" + elementContent[j].year + ")";
                        var venue = ", " + elementContent[j].venue;
                        var publication = ' "' + elementContent[j].publication + '"';
                        var docUrl = elementContent[j].docUrl;

                        if (author.length === 8) {
                            author = "Unknown. ";
                        }

                        var excerptTextNode = document.createTextNode(excerpt);
                        var authorTextNode = document.createTextNode(author);
                        var yearTextNode = document.createTextNode(year);
                        var publicationLink = document.createElement("a");
                        var publicationTextNode = document.createTextNode(publication);
                        publicationLink.href = docUrl;
                        publicationLink.target = "_blank";
                        publicationLink.appendChild(publicationTextNode);
                        var venueTextNode = document.createTextNode(venue);

                        li.appendChild(excerptTextNode);
                        li.appendChild(document.createElement("br"));
                        li.appendChild(authorTextNode);
                        li.appendChild(yearTextNode);
                        li.appendChild(publicationLink);
                        li.appendChild(venueTextNode);
                    }
                }
            }

            if (displayList.mineral.length > 0) {
                var mineralLi = document.createElement("li");
                var mineralUl = document.createElement("ul");
                mineralLi.className = "mte-content-li-root";
                mineralLi.appendChild(document.createTextNode("Mineral: "));
                mineralLi.appendChild(mineralUl);
                mineralLi.appendChild(document.createElement("hr"));
                propertyContentUl.appendChild(mineralLi);
                for (var i = 0; i < displayList.mineral.length; i++) {
                    var mineralName = displayList.mineral[i].component;
                    var mineralContent = displayList.mineral[i].content;
                    var mineralNameLi = document.createElement("li");
                    var mineralNameB = document.createElement("b");
                    mineralNameB.innerHTML = mineralName;
                    var mineralContentOl = document.createElement("ol");
                    mineralNameLi.className = "mte-content-li";
                    mineralNameLi.appendChild(mineralNameB);
                    mineralNameLi.appendChild(mineralContentOl);
                    mineralUl.appendChild(mineralNameLi);

                    for (var j = 0; j < mineralContent.length; j++) {
                        var li = document.createElement("li");
                        li.className = "mte-content-li-property";
                        mineralContentOl.appendChild(li);

                        var excerpt = '"' + mineralContent[j].excerpt + '"';
                        var author = mineralContent[j].primaryAuthor + " et al. ";
                        var year = "(" + mineralContent[j].year + ")";
                        var venue = ", " + mineralContent[j].venue;
                        var publication = ' "' + mineralContent[j].publication + '"';
                        var docUrl = mineralContent[j].docUrl;

                        if (author.length === 8) {
                            author = "Unknown. ";
                        }

                        var excerptTextNode = document.createTextNode(excerpt);
                        var authorTextNode = document.createTextNode(author);
                        var yearTextNode = document.createTextNode(year);
                        var publicationLink = document.createElement("a");
                        var publicationTextNode = document.createTextNode(publication);
                        publicationLink.href = docUrl;
                        publicationLink.target = "_blank";
                        publicationLink.appendChild(publicationTextNode);
                        var venueTextNode = document.createTextNode(venue);

                        li.appendChild(excerptTextNode);
                        li.appendChild(document.createElement("br"));
                        li.appendChild(authorTextNode);
                        li.appendChild(yearTextNode);
                        li.appendChild(publicationLink);
                        li.appendChild(venueTextNode);
                    }
                }
            }

            if (displayList.material.length > 0) {
                var materialLi = document.createElement("li");
                var materialUl = document.createElement("ul");
                materialLi.className = "mte-content-li-root";
                materialLi.appendChild(document.createTextNode("Material: "));
                materialLi.appendChild(materialUl);
                materialLi.appendChild(document.createElement("hr"));
                propertyContentUl.appendChild(materialLi);
                for (var i = 0; i < displayList.material.length; i++) {
                    var materialName = displayList.material[i].component;
                    var materialContent = displayList.material[i].content;
                    var materialNameLi = document.createElement("li");
                    var materialNameB = document.createElement("b");
                    materialNameB.innerHTML = materialName;
                    var materialContentOl = document.createElement("ol");
                    materialNameLi.className = "mte-content-li";
                    materialNameLi.appendChild(materialNameB);
                    materialNameLi.appendChild(materialContentOl);
                    materialUl.appendChild(materialNameLi);

                    for (var j = 0; j < materialContent.length; j++) {
                        var li = document.createElement("li");
                        li.className = "mte-content-li-property";
                        materialContentOl.appendChild(li);

                        var excerpt = '"' + materialContent[j].excerpt + '"';
                        var author = materialContent[j].primaryAuthor + " et al. ";
                        var year = "(" + materialContent[j].year + ")";
                        var venue = ", " + materialContent[j].venue;
                        var publication = ' "' + materialContent[j].publication + '"';
                        var docUrl = materialContent[j].docUrl;

                        if (author.length === 8) {
                            author = "Unknown. ";
                        }

                        var excerptTextNode = document.createTextNode(excerpt);
                        var authorTextNode = document.createTextNode(author);
                        var yearTextNode = document.createTextNode(year);
                        var publicationLink = document.createElement("a");
                        var publicationTextNode = document.createTextNode(publication);
                        publicationLink.href = docUrl;
                        publicationLink.target = "_blank";
                        publicationLink.appendChild(publicationTextNode);
                        var venueTextNode = document.createTextNode(venue);

                        li.appendChild(excerptTextNode);
                        li.appendChild(document.createElement("br"));
                        li.appendChild(authorTextNode);
                        li.appendChild(yearTextNode);
                        li.appendChild(publicationLink);
                        li.appendChild(venueTextNode);
                    }
                }
            }

            if (displayList.feature.length > 0) {
                var featureLi = document.createElement("li");
                var featureUl = document.createElement("ul");
                featureLi.className = "mte-content-li-root";
                featureLi.appendChild(document.createTextNode("Feature: "));
                featureLi.appendChild(featureUl);
                featureLi.appendChild(document.createElement("hr"));
                propertyContentUl.appendChild(featureLi);
                for (var i = 0; i < displayList.feature.length; i++) {
                    var featureName = displayList.feature[i].component;
                    var featureContent = displayList.feature[i].content;
                    var featureNameLi = document.createElement("li");
                    var featureNameB = document.createElement("b");
                    featureNameB.innerHTML = featureName;
                    var featureContentOl = document.createElement("ol");
                    featureNameLi.className = "mte-content-li";
                    featureNameLi.appendChild(featureNameB);
                    featureNameLi.appendChild(featureContentOl);
                    featureUl.appendChild(featureNameLi);

                    for (var j = 0; j < featureContent.length; j++) {
                        var li = document.createElement("li");
                        li.className = "mte-content-li-property";
                        featureContentOl.appendChild(li);

                        var excerpt = '"' + featureContent[j].excerpt + '"';
                        var author = featureContent[j].primaryAuthor + " et al. ";
                        var year = "(" + featureContent[j].year + ")";
                        var venue = ", " + featureContent[j].venue;
                        var publication = ' "' + featureContent[j].publication + '"';
                        var docUrl = featureContent[j].docUrl;

                        if (author.length === 8) {
                            author = "Unknown. ";
                        }

                        var excerptTextNode = document.createTextNode(excerpt);
                        var authorTextNode = document.createTextNode(author);
                        var yearTextNode = document.createTextNode(year);
                        var publicationLink = document.createElement("a");
                        var publicationTextNode = document.createTextNode(publication);
                        publicationLink.href = docUrl;
                        publicationLink.target = "_blank";
                        publicationLink.appendChild(publicationTextNode);
                        var venueTextNode = document.createTextNode(venue);

                        li.appendChild(excerptTextNode);
                        li.appendChild(document.createElement("br"));
                        li.appendChild(authorTextNode);
                        li.appendChild(yearTextNode);
                        li.appendChild(publicationLink);
                        li.appendChild(venueTextNode);
                    }
                }
            }
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