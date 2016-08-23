define([

], function (

) {
    "use strict";

    var MTEViewer = function () {
        this._autoCompletionList = [];

        customizeAutoCompletion();
        initTargetList(this);
        initComponentList(this);
        enableAutoCompletion(this);
        enableSearchButton(this);
        enableStatisticsButton(this);
    }

    //load target names
    function initTargetList (mte) {
        $.ajax({
            url: "http://mte.jpl.nasa.gov/cgi/getTargetsName.py",
            type: "post",
            dataType: "json",
            success: function (returnedList) {
                var targetNames = returnedList.target_name;

                for (var i = 0; i < targetNames.length; i++) {
                    if (isNameInList(targetNames[i][0], mte._autoCompletionList)) {
                        continue;
                    }

                    mte._autoCompletionList.push({
                        label: targetNames[i][0],
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
                        if (isNameInList(targetName, formattedList)) {
                            for (var j = 0; j < formattedList.length; j++) {
                                if (formattedList[j].label === targetName) {
                                    formattedList[j].associates.push({
                                        component: returnedList.results[i][1],
                                        authors: returnedList.results[i][2],
                                        publication: returnedList.results[i][3]
                                    });
                                }
                            }
                        } else {
                            formattedList.push({
                                label: targetName,
                                associates: [{
                                    component: returnedList.results[i][1],
                                    authors: returnedList.results[i][2],
                                    publication: returnedList.results[i][3]
                                }]
                            });
                        }
                    }

                    resultsStatusPanel.innerHTML = formattedList.length + " targets are found."

                    if (formattedList.length > 1) {
                        displayResults(formattedList, "single", mte);
                    } else {
                        displayResults(formattedList, "multiple", mte);
                    }
                }
            });
        }
    }

    function displayResults (formattedList, displayFlag, mte) {
        console.log(formattedList);
        var resultsDiv = document.getElementById("mteResultsDisplay");

        //remove everything in div
        while (resultsDiv.hasChildNodes()) {
            resultsDiv.removeChild(resultsDiv.lastChild);
        }

        for (var i = 0; i < formattedList.length; i++) {
            //target name
            var ul = document.createElement("ul");
            var targetNameLi = document.createElement("li");
            targetNameLi.appendChild(document.createTextNode("Target: " + formattedList[i].label));
            ul.appendChild(targetNameLi);
            resultsDiv.appendChild(ul);

            //properties
            var propertiesLi = document.createElement("li");
            var propertiesEntryUl = document.createElement("ul");
            propertiesLi.appendChild(document.createTextNode("Properties:"));
            propertiesLi.appendChild(propertiesEntryUl);
            ul.appendChild(propertiesLi);

            for (var j = 0; j < formattedList[i].associates.length; j++) {
                var entryLi = document.createElement("li");
                var componentName = formattedList[i].associates[j].component;
                var authors = formattedList[i].associates[j].authors;

                if (authors.length > 20) {
                    authors = authors.substring(0, 20) + ' et al.';
                }

                var entryText = componentName + "  [" + authors +"]"
                entryLi.appendChild(document.createTextNode(entryText));
                propertiesEntryUl.appendChild(entryLi);
            }

            //publications
            var publicationsLi = document.createElement("li");
            var publicationsEntryUl = document.createElement("ul");
            publicationsLi.appendChild(document.createTextNode("Publications:"));
            publicationsLi.appendChild(publicationsEntryUl);
            ul.appendChild(publicationsLi);

            for (var j = 0; j < formattedList[i].associates.length; j++) {
                var entryLi = document.createElement("li");
                var publicationTitle = formattedList[i].associates[j].publication;
                var authors = formattedList[i].associates[j].authors;

                if (authors.length > 20) {
                    authors = authors.substring(0, 20) + ' et al.';
                }

                var entryText = authors + ', "' + publicationTitle + '"';
                var perviousEntryLi = publicationsEntryUl.lastChild;
                if (perviousEntryLi !== null && perviousEntryLi.innerHTML === entryText){
                    continue;
                }

                entryLi.appendChild(document.createTextNode(entryText));
                publicationsEntryUl.appendChild(entryLi);
            }

            //related images
            var imagesLi = document.createElement("li");
            var imagesEntryUl = document.createElement("ul");
            imagesLi.appendChild(document.createTextNode("Related Images:"));
            imagesLi.appendChild(imagesEntryUl);
            ul.appendChild(imagesLi);

            //TODO fake images URL.
            var imagesContainerLi = document.createElement("li");
            var imagesContainerDiv = document.createElement("div");
            imagesContainerDiv.className = "mte-related-images-div";
            imagesContainerLi.appendChild(imagesContainerDiv);
            imagesEntryUl.appendChild(imagesContainerLi);

            for (var j = 0; j < 8; j++) {
                var imageSubDiv = document.createElement("div");
                var img = document.createElement("img");
                imageSubDiv.className = "mte-related-images-subdiv";
                img.src = "https://an.rsl.wustl.edu/msl/mslbrowser/labelfeattarg.aspx?i=104664&size=150&show=False";
                imageSubDiv.appendChild(img);
                imagesContainerDiv.appendChild(imageSubDiv);
            }
        }

    }

    function enableStatisticsButton(mte) {
        $('#statisticsButton').click(function () {
            $('#statisticsDisplay').highcharts({
                chart: {
                    type: 'column'
                },
                title: {
                    text: ''
                },
                xAxis: {
                    categories: ['Target', 'Element', 'Feature', 'Material', 'Mineral', 'Document', 'Event'],
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
                    data: [200, 250, 232, 125, 209, 60, 500]

                }]
            });
        });
    }

    return MTEViewer;
});