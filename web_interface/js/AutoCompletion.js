define([
    'Constants',
    'Util'
], function (
    CONSTANTS,
    Util
) {
    "use strict";

    var AutoCompletion = function (cgiRoot){
        this._list = [];

        customize();
        loadTargets(this._list, cgiRoot);
        loadComponents(this._list, cgiRoot);
        loadPrimaryAuthor(this._list, cgiRoot);
    }

    AutoCompletion.prototype.enable = function (targetElement) {
        var self = this;
        $(targetElement).catcomplete({
            delay: 0,
            source: self._list
        });
    }

    function customize () {
        $.widget("custom.catcomplete", $.ui.autocomplete, {
            _create: function() {
                this._super();
                this.widget().menu("option", "items", "> :not(.ui-autocomplete-category)");
            },
            _renderMenu: function(ul, items) {
                var that = this,
                    currentCategory = "";
                $.each( items, function(index, item) {
                    var li;
                    if (item.category != currentCategory) {
                        ul.append("<li class='ui-autocomplete-category'>" + item.category + "</li>");
                        currentCategory = item.category;
                    }
                    li = that._renderItemData(ul, item);
                    if (item.category) {
                        li.attr("aria-label", item.category + " : " + item.label);
                    }
                });
            }
        });
    }

    function loadTargets (list, cgiRoot) {
        $.ajax({
            url: cgiRoot + CONSTANTS.SERVER_GET_TARGETS,
            type: "post",
            dataType: "json",
            success: function (returnedList) {
                targetsCallback(returnedList, list);
            }
        });
    }

    function targetsCallback (returnedList, list) {
        var results = returnedList.target_name;
        var util = new Util();

        for (var i = 0; i < results.length; i++) {
            if (util.isNameInList(results[i][0], list, "label")) {
                continue;
            }

            list.push({
                label: results[i][0],
                category: "Target"
            });
        }
    }

    function loadComponents (list, cgiRoot) {
        $.ajax({
            url: cgiRoot + CONSTANTS.SERVER_GET_COMPONENTS,
            type: "post",
            dataType: "json",
            success: function (returnedList) {
                componentsCallback(returnedList, list)
            }
        });
    }

    function componentsCallback(returnedList, list) {
        var results = returnedList.results;
        var util = new Util();

        for (var i = 0; i < results.length; i++) {
            if (util.isNameInList(results[i][0], list, "label")) {
                continue;
            }

            list.push({
                label: results[i][0],
                category: results[i][1]
            });
        }
    }

    function loadPrimaryAuthor (list, cgiRoot) {
        $.ajax({
            url: cgiRoot + CONSTANTS.SERVER_GET_PRIMARY_AUTHOR,
            type: "post",
            dataType: "json",
            success: function (returnedList) {
                primaryAuthorCallback(returnedList, list)
            }
        });
    }

    function primaryAuthorCallback (returnedList, list) {
        var results = returnedList.primary_author;
        var util = new Util();

        for (var i = 0; i < results.length; i++) {
            if (util.isNameInList(results[i][0], list, "label")) {
                continue;
            }

            list.push({
                label: results[i][0],
                category: "Primary Author"
            });
        }
    }

    return AutoCompletion;
})