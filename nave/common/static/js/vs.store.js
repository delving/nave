/**
 * Store will save in either the local sessionStorage or in a session cookie
 */

var Store = (function () {
    'use strict'
    var Global = typeof window !== 'undefined' ? window : document
    var doc = Global.document
    var methods = {}

    // Session Storage
    if (typeof Storage !== 'undefined') {
        function sessionStorage() {
            return Global.sessionStorage
        }

        methods.get = function (key) {
            var data = sessionStorage().getItem(key)
            if (data) {
                // check if it is json - start with '{' - stringify if so, otherwise leave as as and return
                var typedData = data.charAt(0) === '{' ? JSON.parse(data) : data
                return typedData
            } else {
                return undefined
            }
        }

        methods.set = function (key, data) {
            // check if it is json - start with '{' - stringify if so, otherwise leave as as and return
            var typedData =
                JSON.stringify(data).charAt(0) === '{'
                    ? JSON.stringify(data)
                    : data
            return sessionStorage().setItem(key, typedData)
        }

        methods.remove = function (key) {
            return sessionStorage().removeItem(key)
        }

        // methods.clearAll = function () {
        //     return sessionStorage().clear()
        // }
    }
    // Cookie Storage
    else {
        methods.get = function (key) {
            if (!key) {
                return
            }
            var matches = doc.cookie.match(
                new RegExp(
                    '(?:^|; )' +
                        key.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') +
                        '=([^;]*)'
                )
            )
            if (matches) {
                var match = decodeURIComponent(matches[1])
                // check if it is json - start with '{' - parse if so, otherwise leave as as and return
                return match.charAt(0) === '{' ? JSON.parse(match) : match
            } else {
                return undefined
            }
        }

        methods.set = function (key, data) {
            if (!key || !data) {
                return
            }
            // check if it is json - start with '{' - stringify if so, otherwise leave as as and return
            var cData =
                JSON.stringify(data).charAt(0) === '{'
                    ? JSON.stringify(data)
                    : data
            // set cookie
            doc.cookie =
                encodeURIComponent(key) +
                '=' +
                encodeURIComponent(cData) +
                '; path=/; samesite=lax' // no expiration date - session only
        }

        methods.remove = function (key) {
            if (!key) {
                return
            }
            doc.cookie =
                escape(key) +
                '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; samesite=lax'
        }
    }

    return methods
})()
window['Store'] = Store
