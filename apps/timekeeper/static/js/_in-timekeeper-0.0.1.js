#!/usr/bin/env node
/*  _node-timekeeper
    requires() node-based modules for the time keeper app.
    This file must be browserified to ./timekeeper.js.
    -Christopher Welborn 01-19-2016
*/

/* jshint node:true, esnext:true, moz:true */

'use strict';
var Moment = require('moment-datetime'); // eslint-disable-line no-unused-vars

var tktools = { // eslint-disable-line no-unused-vars
    version: '0.0.1',
    parse_datetime: function parse_datetime(s) {
        /* Parse a datetime in TK format (from python).
           See format in apps.timekeeper.models.TKSession: '%m-%d-%Y %I:%M%p'
        */
        return new Moment().strptime(s, '%m-%d-%Y %I:%M%p');
    }
};
