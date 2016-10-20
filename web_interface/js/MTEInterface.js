define([
    'Constants'
], function (
    CONSTANTS
) {
    "use strict";

    var MTEInterface = function (containerId, thumbnailUrlRoot, mslANLinkRoot) {
        this._thumbnailUrlRoot = thumbnailUrlRoot;
        this._mslANLinkRoot = mslANLinkRoot;
        this._mteContainer = document.getElementById(containerId);
        this._mteLogo = document.createElement("div");
        this._mteSubtitle = document.createElement("div");
        this._mteSearch = document.createElement("div");
        this._mteResults = document.createElement("div");
        this._mteSearchComponent = document.createElement("div");
        this._inputField = document.createElement("input");
        this._buttonSpan = document.createElement("span");
        this._searchButton = createButton(CONSTANTS.SEARCHBUTTON_ID, CONSTANTS.SEARCHBUTTON_STYLE,
            CONSTANTS.SEARCHBUTTON_IMG);
        this._statisticsButton = createButton(CONSTANTS.STATSBUTTON_ID, CONSTANTS.STATSBUTTON_STYLE,
            CONSTANTS.STATSBUTTON_IMG, CONSTANTS.STATSBUTTON_DATA_TARGET);
        this._mteResultsStatus = document.createElement("div");
        this._mteResultsDisplay = document.createElement("div");

        return this;
    }

    MTEInterface.prototype.build = function () {
        this._mteLogo.className = CONSTANTS.LOGO_STYLE;
        this._mteSubtitle.className = CONSTANTS.SUBTITLE_STYLE;
        this._mteSearch.className = CONSTANTS.SEARCH_STYLE;
        this._mteResults.className = CONSTANTS.RESULTS_STYLE;
        this._mteContainer.appendChild(this._mteLogo);
        this._mteContainer.appendChild(this._mteSubtitle);
        this._mteContainer.appendChild(this._mteSearch);
        this._mteContainer.appendChild(this._mteResults);

        //logo panel
        this._mteLogo.appendChild(document.createTextNode(CONSTANTS.LOGO_STR));

        //subtitle panel
        this._mteSubtitle.appendChild(document.createTextNode(CONSTANTS.SUBTITLE_STR));
        this._mteSubtitle.appendChild(document.createElement("br"));
        this._mteSubtitle.appendChild(document.createTextNode(CONSTANTS.HOLDINGS_STR));

        //search panel
        this._mteSearchComponent.className = CONSTANTS.SEARCHCOMP_STYPE;
        this._inputField.type = "text";
        this._inputField.className = CONSTANTS.INPUTFIELD_STYLE;
        this._inputField.id = CONSTANTS.INPUTFIELD_ID;
        this._inputField.placeholder = CONSTANTS.INPUTFIELD_PLACEHOLDER_STR;
        this._buttonSpan.className = CONSTANTS.BUTTON_SPAN_STYLE;
        this._mteSearch.appendChild(this._mteSearchComponent);
        this._mteSearchComponent.appendChild(this._inputField);
        this._mteSearchComponent.appendChild(this._buttonSpan);
        this._buttonSpan.appendChild(this._searchButton);
        this._buttonSpan.appendChild(this._statisticsButton);

        //results panel
        this._mteResultsStatus.id = CONSTANTS.RESULTS_STATUS_ID;
        this._mteResultsStatus.className = CONSTANTS.RESULTS_STATUS_STYLE;
        this._mteResultsDisplay.id = CONSTANTS.RESULTS_DISPLAY_ID;
        this._mteResultsDisplay.className = CONSTANTS.RESULTS_DISPLAY_STYLE;
        this._mteResults.appendChild(this._mteResultsStatus);
        this._mteResults.appendChild(this._mteResultsDisplay);
    }

    MTEInterface.prototype.setStatusLabel = function (statusStr) {
        this._mteResultsStatus.innerHTML = statusStr;
    }

    MTEInterface.prototype.removeAllPreviousResults = function () {
        while (this._mteResultsDisplay.hasChildNodes()) {
            this._mteResultsDisplay.removeChild(this._mteResultsDisplay.lastChild);
        }
    }

    MTEInterface.prototype.displayResults = function (formattedList, mteListener, util) {
        for (var i = 0; i < formattedList.length; i++) {
            //unit result container
            var resultBlock = document.createElement("div");
            resultBlock.className = "mte-results-display-block"
            this._mteResultsDisplay.appendChild(resultBlock);

            //thumbnail image
            var thumbnailDiv = document.createElement("div");
            var thumbnailImg = document.createElement("img");
            thumbnailDiv.className = "mte-results-display-block-img";
            $(thumbnailDiv).attr("data-toggle", "modal");
            $(thumbnailDiv).attr("data-target", "#singleTargetDiv");
            if (formattedList[i].id !== undefined && formattedList[i].id !== "None") {
                thumbnailImg.src = this._thumbnailUrlRoot + formattedList[i].id;
            } else {
                thumbnailImg.src = "images/empty_placeholder.png";
            }
            thumbnailDiv.appendChild(thumbnailImg);
            resultBlock.appendChild(thumbnailDiv);
            if (formattedList[i].id !== undefined && formattedList[i].id !== "None") {
                resultBlock.thumbnailUrl = this._thumbnailUrlRoot + formattedList[i].id;
                resultBlock.anLink = this._mslANLinkRoot + formattedList[i].id;
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
            var nonDuplicatePublicationList = util.getNonDuplicatePublication(formattedList[i].associates);
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
            var msnry = new Masonry(this._mteResultsDisplay, {
                itemSelector: ".mte-results-display-block",
                columnWidth: 244,
                gutter: 10
            });

            //attach target name click event
            mteListener.appendTargetClickEventListener(targetDiv, resultBlock);
            mteListener.appendTargetClickEventListener(thumbnailDiv, resultBlock);
        }
    }

    MTEInterface.prototype.buildSingleTargetPage = function (resultBlock, displayList, mteListener) {
        var targetName = resultBlock.targetName;
        var thumbnailUrl = resultBlock.thumbnailUrl;
        var anLink = resultBlock.anLink;
        var divHeader = document.getElementById("singleTargetDivHeader");
        var divDisplay = document.getElementById("singleTargetDivDisplay");

        removeAllFromSingleTargetPage(divHeader, divDisplay);

        //thumbnail
        var thumbnail = document.createElement("img");
        thumbnail.id = "targetThumbnail";
        thumbnail.src = thumbnailUrl;
        divHeader.appendChild(thumbnail);

        //target name
        var h4 = document.createElement("h4");
        h4.id = "targetTitle";
        h4.appendChild(document.createTextNode(targetName));
        divHeader.appendChild(h4);

        //share button
        var url = location.href;
        url = url + "?lookup=" + targetName;
        var shareDiv = document.createElement("div");
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
        mteListener.appendShareButtonEventListener(shareButton, shareInput);

        //anButton
        if (anLink !== undefined && anLink.length > 0) {
            var anButton = document.createElement("input");
            anButton.type = "button";
            anButton.className = "btn btn-info btn-sm";
            anButton.id = "anButton";
            anButton.value = "Go to MSL Analyst's Notebook"
            divHeader.appendChild(anButton);
            mteListener.appendANLinkEventListener(anButton, anLink);
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

        if (displayList.element.length > 0) {
            buildPropertyComponent(propertyContentUl, displayList);
        }

        if (displayList.mineral.length > 0) {
            buildPropertyMineral(propertyContentUl, displayList);
        }

        if (displayList.material.length > 0) {
            buildPropertyMaterial (propertyContentUl, displayList);
        }

        if (displayList.feature.length > 0) {
            buildPropertyFeature (propertyContentUl, displayList);
        }

        ///////////testing mmgis//////////////////////////////////
        ////1st method////
        //var mmgisDiv = document.createElement('div');
        //mmgisDiv.className = 'mte-mmgis-div';
        //divDisplay.appendChild(mmgisDiv);
        //$.ajax({
        //    url: "http://miplmmgis.jpl.nasa.gov/mmgis/MMWebGIS/Missions/MSL/MSL.html",
        //    //url: "http://miplmmgis.jpl.nasa.gov/mmgis/MMWebGIS/Missions/MSL/Layers/ChemCam/MSL_CHEMCAM_oxides_sol1126_geo.json",
        //    success: function (mmgisPage){
        //        mmgisDiv.innerHTML = mmgisPage;
        //    }
        //});
        ////1st method end/////

        ////2nd method/////////
        //$(mmgisDiv).load("http://miplmmgis.jpl.nasa.gov/mmgis/MMWebGIS/Missions/MSL/MSL.html");
        ////2nd method end//////

        ////3rd method/////////
        var mmgisDiv = document.createElement('div');
        mmgisDiv.className = 'mte-mmgis-div';
        divDisplay.appendChild(mmgisDiv);

        var iframe = document.createElement("iframe");
        iframe.className = "mte-mmgis-iframe";
        iframe.src = "http://miplmmgis.jpl.nasa.gov/mmgis/MMWebGIS/Missions/MSL/MSL.html";
        mmgisDiv.appendChild(iframe);

        $("#searchTool").click();
        $("#searchToolB").click();
        $("#auto_search").val("Windjana 614");
        $("#searchToolSelect").click();
        ////3rd method end/////
        ///////////testing mmgis end//////////////////////////////
    }

    MTEInterface.prototype.createColumnChart = function (statisticList) {
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
                data: statisticList
            }]
        });
    }

    function buildPropertyComponent (propertyContentUl, displayList) {
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

    function buildPropertyMineral (propertyContentUl, displayList) {
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

    function buildPropertyMaterial (propertyContentUl, displayList) {
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

    function buildPropertyFeature (propertyContentUl, displayList) {
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

    function removeAllFromSingleTargetPage (divHeader, divDisplay) {
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
    }

    function createButton (buttonId, buttonStyle, buttonImg, dataTarget) {
        var button = document.createElement("button");
        button.type = "button";
        button.id = buttonId;
        button.className = buttonStyle;
        var buttonImgElem = document.createElement("img");
        buttonImgElem.src = buttonImg;
        buttonImgElem.height = "15";
        button.appendChild(buttonImgElem);

        if (dataTarget !== undefined && dataTarget.length > 0) {
            $(button).attr("data-toggle", "modal");
            $(button).attr("data-target", "#" + dataTarget);
        }

        return button;
    }

    return MTEInterface;
})
