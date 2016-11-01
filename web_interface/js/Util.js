define([], function () {
   "use strict";
   var Util = function () {}

   Util.prototype.isNameInList = function (targetName, list, identity) {
      var flag = false;

      for (var i = 0; i < list.length; i++) {
         if (list[i][identity] === targetName) {
            flag = true;
            break;
         }
      }

      return flag;
   }

   Util.prototype.getTargetMatches = function (autoCompletionList, targetName) {
      var targetMatches = 0;

      for (var i = 0; i < autoCompletionList.length; i++) {
         if (autoCompletionList[i].label.toLowerCase() === targetName &&
             autoCompletionList[i].category === "Target") {
               targetMatches++;
         }
      }

      return targetMatches;
   }

   Util.prototype.getComponentMatches = function (autoCompletionList, targetName) {
      var componentMatches = 0;

      for (var i = 0; i < autoCompletionList.length; i++) {
         if (autoCompletionList[i].label.toLowerCase() === targetName &&
             autoCompletionList[i].category !== "Target") {
            componentMatches++;
         }
      }

      return componentMatches;
   }

   Util.prototype.getReformattedList = function (list) {
      var formattedList = [];

      for (var i = 0; i < list.results.length; i++) {
         var targetName = list.results[i][0];
         var targetId = list.results[i][1];
         var targetFirstSol = list.results[i][2];
         var targetLat = list.results[i][11];
         var targetLon = list.results[i][12];
         if (this.isNameInList(targetName, formattedList, "label")) {
            for (var j = 0; j < formattedList.length; j++) {
               if (formattedList[j].label !== targetName) {
                  continue;
               }

               formattedList[j].associates.push({
                  component: list.results[i][3],
                  componentLabel: list.results[i][4],
                  primaryAuthor: list.results[i][5],
                  publication: list.results[i][6],
                  excerpt: list.results[i][7],
                  year: list.results[i][8],
                  venue: list.results[i][9],
                  docUrl: list.results[i][10]
               });
            }
         } else {
            formattedList.push({
               label: targetName,
               id: targetId,
               firstSol: targetFirstSol,
               targetLat: targetLat,
               targetLon: targetLon,
               associates: [{
                  component: list.results[i][3],
                  componentLabel: list.results[i][4],
                  primaryAuthor: list.results[i][5],
                  publication: list.results[i][6],
                  excerpt: list.results[i][7],
                  year: list.results[i][8],
                  venue: list.results[i][9],
                  docUrl: list.results[i][10]
               }]
            });
         }
      }

      return formattedList;
   }

   Util.prototype.addResultsToList = function (returnedList, formattedList) {
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
   }

   Util.prototype.getDisplayList = function (resultBlock) {
      var displayList = {element: [], mineral: [], material: [], feature: []};

      for (var i = 0; i < resultBlock.associates.length; i++) {
         var component = resultBlock.associates[i].component;
         var componentLabel = resultBlock.associates[i].componentLabel.toLocaleLowerCase();

         if (displayList[componentLabel] === undefined) {
            continue;
         }

         if (this.isNameInList(component, displayList[componentLabel], "component")) {
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

      return displayList;
   }

   Util.prototype.getNonDuplicatePublication = function (associatesList) {
      var nonDuplicatePublicationList = [];

      for (var i = 0; i < associatesList.length; i++) {
         var publicationTitle = associatesList[i].publication;

         if (nonDuplicatePublicationList.indexOf(publicationTitle) <= -1) {
            nonDuplicatePublicationList.push(publicationTitle);
         }
      }

      return nonDuplicatePublicationList;
   }

   Util.prototype.getStatisticList = function (dictionary) {
      var statisticList = [];

      statisticList.push(dictionary.document_count[0][0]);
      statisticList.push(dictionary.target_count[0][0]);
      statisticList.push(dictionary.event_count[0][0]);
      statisticList.push(dictionary.element_count[0][0]);
      statisticList.push(dictionary.feature_count[0][0]);
      statisticList.push(dictionary.material_count[0][0]);
      statisticList.push(dictionary.mineral_count[0][0]);

      return statisticList;
   }

   Util.prototype.sortBy = function (field, reverse, primer) {
      var key = function (x) {return primer ? primer(x[field]) : x[field]};

      return function (a,b) {
         var A = key(a), B = key(b);
         return ( (A < B) ? -1 : ((A > B) ? 1 : 0) ) * [-1,1][+!!reverse];
      }
   }

   Util.prototype.getBoundingbox = function (formattedList) {
      var west = Number.MAX_VALUE;
      var east = -Number.MAX_VALUE;
      var south = Number.MAX_VALUE;
      var north = -Number.MAX_VALUE;

      for (var i = 0; i < formattedList.length; i++) {
         var targetLat = formattedList[i].targetLat;
         var targetLon = formattedList[i].targetLon;

         if (targetLat === "None" || targetLon === "None") {
            continue;
         }

         if (targetLat <= south) {
            south = targetLat;
         }

         if (targetLat >= north) {
            north = targetLat;
         }

         if (targetLon <= west) {
            west = targetLon;
         }

         if (targetLon >= east) {
            east = targetLon;
         }
      }

      return {
         west: west,
         east: east,
         south: south,
         north: north
      }
   }

   Util.prototype.getCenterLat = function (boundingbox) {
      return (boundingbox.north + boundingbox.south) / 2;
   }

   Util.prototype.getCenterLon = function (boundingbox) {
      return (boundingbox.east + boundingbox.west) / 2;
   }

   Util.prototype.getZoomlevel = function (boundingbox) {
      //based on the zoom level statistics of openstreetmap provided in
      //http://wiki.openstreetmap.org/wiki/Zoom_levels, we construct a
      //zoomlevel : degree arrays.
      //Note that we only use the zoom levels 8-19.
      var openstreetmapZoomlevel = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19];
      var openstreetmapDegree = [1.406, 0.703, 0.352, 0.176, 0.088, 0.044, 0.022, 0.011, 0.005, 0.003, 0.001, 0.0005];
      var horizonDistance = boundingbox.east  - boundingbox.west;
      var verticalDistance = boundingbox.north - boundingbox.south;
      var referenceDistance = horizonDistance >= verticalDistance ? horizonDistance : verticalDistance;

      for (var i = openstreetmapDegree.length - 1; i >= 0; i--) {
         if (referenceDistance > openstreetmapDegree[i]) {
            continue;
         }

         return openstreetmapZoomlevel[i];
      }
   }

   return Util;
});