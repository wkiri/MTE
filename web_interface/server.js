/*global require,__dirname*/
/*jshint es3:false*/
var connect = require('connect');
connect.createServer(
    connect.static(__dirname)
//    connect.static('SVG')
).listen(8080);
console.log('listening port: 8080');