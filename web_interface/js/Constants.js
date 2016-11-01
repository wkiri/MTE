define([], function () {
    "use strict";
    var CONSTANTS = function () {};
    CONSTANTS.NORMAL_VIEW = "normalVIew";
    CONSTANTS.LOOKUP_VIEW = "lookupView";
    CONSTANTS.LOGO_STR = "Mars Target Encyclopedia";
    CONSTANTS.SUBTITLE_STR = "Compositional information from publications about MSL ChemCam surface targets";
    CONSTANTS.HOLDINGS_STR = "Publications currently indexed: abstracts from LPSC 2015 and 2016";
    CONSTANTS.LOGO_STYLE = "mte-logo";
    CONSTANTS.SUBTITLE_STYLE = "mte-subtitle";
    CONSTANTS.SEARCH_STYLE = "mte-search";
    CONSTANTS.RESULTS_STYLE = "mte-results";
    CONSTANTS.MMGIS_STYLE = "mte-mmgis";
    CONSTANTS.SEARCHBUTTON_ID = "searchButton";
    CONSTANTS.SEARCHBUTTON_STYLE = "btn btn-info";
    CONSTANTS.SEARCHBUTTON_IMG = "images/search-icon.png";
    CONSTANTS.STATSBUTTON_ID = "statisticsButton";
    CONSTANTS.STATSBUTTON_STYLE = "btn btn-info";
    CONSTANTS.STATSBUTTON_IMG = "images/statistics.png";
    CONSTANTS.STATSBUTTON_DATA_TARGET = "statistics-results";
    CONSTANTS.SEARCHCOMP_STYPE = "mte-search-component input-group col-lg-9";
    CONSTANTS.INPUTFIELD_ID = "mteSearchInput";
    CONSTANTS.INPUTFIELD_STYLE = "form-control";
    CONSTANTS.INPUTFIELD_PLACEHOLDER_STR = "Enter target or component name";
    CONSTANTS.BUTTON_SPAN_STYLE = "input-group-btn";
    CONSTANTS.RESULTS_STATUS_ID = "mteResultsStatus";
    CONSTANTS.RESULTS_STATUS_STYLE = "mte-results-status";
    CONSTANTS.RESULTS_DISPLAY_ID = "mteResultsDisplay";
    CONSTANTS.RESULTS_DISPLAY_STYLE = "mte-results-display";
    CONSTANTS.MMGIS_IFRAME_STYLE = "mte-mmgis-iframe";
    CONSTANTS.SERVER_GET_TARGETS = "getTargetsName.py";
    CONSTANTS.SERVER_GET_COMPONENTS = "getComponentsNameAndLabel.py";
    CONSTANTS.SERVER_GET_RESULTS_BY_SEARCHSTR = "getResultsBySearchStr.py";
    CONSTANTS.SERVER_GET_STATISTIC = "getStatistics.py";
    CONSTANTS.SERVER_GET_RESULTS_WITHOUT_PROPERTIES = "getResultsWOProperties.py";

    return CONSTANTS;
})