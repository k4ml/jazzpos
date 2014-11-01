var xposApp = angular.module('xposApp', ['ngResource']);

xposApp.config(function($interpolateProvider, $httpProvider, $provide) {
    var $http, interceptor;

    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');

    $provide.factory('requestInterceptor', function ($q, $injector) {
        var notificationChannel;
        
        function requestEnded () {
            // get $http via $injector because of circular dependency problem
            $http = $http || $injector.get('$http');
            // don't send notification until all requests are complete
            if ($http.pendingRequests.length < 1) {
                // get requestNotificationChannel via $injector because of circular dependency problem
                notificationChannel = notificationChannel || $injector.get('requestNotificationChannel');
                // send a notification requests are complete
                notificationChannel.requestEnded();
            }
        }

        return {
            request: function (config) {
                notificationChannel = notificationChannel || $injector.get('requestNotificationChannel');
                notificationChannel.requestStarted();
                return config;
            },
            requestError: function (rejection) {
                requestEnded();
                return $q.reject(rejection);
            },
            response: function (response) {
                requestEnded();
                return response;
            },
            responseError: function (rejection) {
                requestEnded();
                return $q.reject(rejection);
            }
        }
    });
    $httpProvider.interceptors.push('requestInterceptor');

});

xposApp.factory('requestNotificationChannel', ['$rootScope', function($rootScope){
    // private notification messages
    var _START_REQUEST_ = '_START_REQUEST_';
    var _END_REQUEST_ = '_END_REQUEST_';

    // publish start request notification
    var requestStarted = function() {
        $rootScope.$broadcast(_START_REQUEST_);
    };
    // publish end request notification
    var requestEnded = function() {
        $rootScope.$broadcast(_END_REQUEST_);
    };
    // subscribe to start request notification
    var onRequestStarted = function($scope, handler){
        $scope.$on(_START_REQUEST_, function(event){
            handler();
        });
    };
    // subscribe to end request notification
    var onRequestEnded = function($scope, handler){
        $scope.$on(_END_REQUEST_, function(event){
            handler();
        });
    };

    return {
        requestStarted:  requestStarted,
        requestEnded: requestEnded,
        onRequestStarted: onRequestStarted,
        onRequestEnded: onRequestEnded
    };
}]);

xposApp.directive('loadingWidget', ['requestNotificationChannel', function (requestNotificationChannel) {
    return {
        restrict: "A",
        link: function (scope, element) {
            // hide the element initially
            element.hide();

            var startRequestHandler = function() {
                // got the request start notification, show the element
                element.show();
            };

            var endRequestHandler = function() {
                // got the request start notification, show the element
                element.hide();
            };

            requestNotificationChannel.onRequestStarted(scope, startRequestHandler);

            requestNotificationChannel.onRequestEnded(scope, endRequestHandler);
        }
    };
}]);

xposApp.filter('startFrom', function () {
    return function (input, start) {
        start = +start; //parse to int
        return input.slice(start);
    }
});

xposApp.factory('xposapp', function($http, $location) {
    var self = this;
    var default_headers = {
        Accept: 'application/json',
        'Content-Type': 'application/json'
    }

    function getOrderID() {
        var orderID = $location.$$absUrl.split('/').slice(-2, -1);
        return parseInt(orderID);
    }

    function getOrderURL() {
        var orderID = getOrderID();
        return '/pos/api/order/' + orderID + '/'
    }

    function do_GET(path, params, success_cb) {
        $http({
            method: 'GET',
            url: path,
            params: params,
            headers: default_headers
        }).success(function(data, status, headers, config) {
            success_cb(data);
        }).error(function(data, status, headers, config) {
            console.log(data);
        });
    }

    function do_POST(path, data, success_cb, error_cb) {
        $http({
            method: 'POST',
            url: path,
            data: data,
            headers: default_headers,
            xsrfHeaderName: 'X-CSRFToken',
            xsrfCookieName: 'csrftoken'
        }).success(function(data, status, headers, config) {
            success_cb(data);
        }).error(function(data, status, headers, config) {
            error_cb(data, status);
        });
    }

    return {
        get: do_GET,
        post: do_POST,
        getOrderURL: getOrderURL,
        getOrderID: getOrderID
    }
});

xposApp.factory('checklist', function() {
    var self = this;

    function updateSelected (theList, action, id, itemIndex, updateCallback) {
        if (action == 'add') {
            theList[itemIndex].selected = true;
        }
        if (action == 'remove') {
            theList[itemIndex].selected = false;
        }
        updateCallback(itemIndex);
    }

    function updateSelection (theList, $event, id, itemIndex, updateCallback) {
        var checkbox = $event.target;
        var action = (checkbox.checked ? 'add' : 'remove');
        updateSelected(theList, action, id, itemIndex, updateCallback);
    }

    function selectAll (theList, $event, updateCallback) {
        var checkbox = $event.target;
        var action = (checkbox.checked ? 'add' : 'remove');
        for (var i = 0; i < theList.length; i++) {
            var entity = theList[i];
            updateSelected(theList, action, entity.id, i, updateCallback);
        }
    }

    function isSelected (theList, id) {
        for (var i = 0; i < theList.length; i++) {
            var entity = theList[i];
            if (entity.id == id) {
                return entity.selected == true;
            }
        }
        return false;
    }

    function getSelectedClass (entity) {
        return isSelected(entity.id) ? 'selected' : '';
    }

    //something extra I couldn't resist adding
    function isSelectedAll () {
        if ($scope.order != undefined) {
            return $scope.selected.length === $scope.order.items.length;
        }
    }

    return {
        getSelectedClass: getSelectedClass,
        updateSelected: updateSelected,
        updateSelection: updateSelection,
        isSelected: isSelected,
        selectAll: selectAll
    }

});

xposApp.controller('OrderEditController', function($scope, xposapp, checklist) {
    $scope.checklist = checklist
    $scope.post_status = [];
    $scope.selected = [];
    xposapp.getOrderID();
    xposapp.get(xposapp.getOrderURL(), {}, function(data) {
        $scope.order = data;
    });

    function updateTotal() {
        var total = 0;
        for (var i = 0; i < $scope.order.items.length; i++) {
            total += parseFloat($scope.order.items[i].total);
        }
        $scope.order.total = total;
    }

    function updateItemTotal(itemIndex) {
        var item = $scope.order.items[itemIndex]
        if (item.selected === true) {
            $scope.order.items[itemIndex].total = item.qty * item.price;
        }
        else {
            $scope.order.items[itemIndex].total = 0;
        }
        updateTotal();
    }
    $scope.updateItemTotal = updateItemTotal

    $scope.save = function() {
        xposapp.post(xposapp.getOrderURL(), $scope.order, function(data) {
            $scope.post_status = data;   
        },
        function(data, status) {
            if (status == 500) {
                $scope.post_status = ["Internal server error " + status];   
            }
            else {
                $scope.post_status = data;
            }
        });
    }
});

xposApp.controller('OrderViewController', function($scope) {

});

xposApp.controller('StockEditController', function($scope, xposapp, checklist) {
    $scope.checklist = checklist;

    function getItems() {
        xposapp.get('/pos/api/stocks/', {}, function(data) {
            $scope.data = data
            $scope.items = data['items'];
        });
    }
    getItems();

    function updateTotal() {
        var total = 0;
        for (var i = 0; i < $scope.items.length; i++) {
            total += parseFloat($scope.items[i].total);
        }
        $scope.total = total;
    }

    function updateItemTotal(itemIndex) {
        var item = $scope.items[itemIndex]
        if (item.selected === true) {
            $scope.items[itemIndex].total = item.qty * item.price;
        }
        else {
            $scope.items[itemIndex].total = 0;
        }
        updateTotal();
    }
    $scope.updateItemTotal = updateItemTotal

    $scope.save = function() {
        xposapp.post('/pos/api/stocks/', $scope.items, function(data) {
            $scope.post_status = data;   
            getItems();
            $scope.total = 0;
        },
        function(data, status) {
            if (status == 500) {
                $scope.post_status = ["Internal server error " + status];   
            }
            else {
                $scope.post_status = data;
            }
        });
    }

});

xposApp.run(function($rootScope) {
    $rootScope.go = function(url) {
        window.location = url;
    }
});
