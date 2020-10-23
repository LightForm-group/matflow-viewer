$(document).ready(function () {

    $(document).click(function (evt) {

        if (evt.target.id == "all-tasks-button") {
            $('#task-list-wrapper').toggleClass('my-modal');
            return;
        }

        if ($('#task-list-wrapper').hasClass('my-modal')) {

            if (evt.target.id == "task-list-wrapper")
                return;

            $('#task-list-wrapper').toggleClass('my-modal');

        };
    });


    // Handle clicking to change figure:
    $('.fig-wrapper').click(function (evt) {
        var workflowID = $(this).data('wid');
        var figIdx = $(this).data("fig-idx");
        var data = {
            "workflowID": workflowID,
            "figIdx": figIdx,
        };
        var newURL = "/workflow/" + workflowID + "/figures/" + figIdx
        changeFigure(data);
        history.pushState(data, "", newURL);
    });

    // Handle clicking to change task:
    $('.task-wrapper:not(.figure)').click(function (evt) {
        var workflowID = $(this).data('wid');
        var taskIdx = $(this).data("task-idx");
        var data = {
            "workflowID": workflowID,
            "taskIdx": taskIdx,
            "elementIdx": 0,
            "inputName": null,
            "outputName": null,
            "fileName": null,
        };
        var newURL = "/workflow/" + workflowID + "/task/" + taskIdx + "/element/0"
        changeTask(data);
        history.pushState(data, "", newURL);
    });

    // Handle clicking to change input/output/file parameter:
    $('.task-inspector').on('click', '.task-param-name', function (event) {

        var paramType = $(this).data('param-type');
        var paramName = $(this).data('param-name');
        var workflowID = $(this).data('wid');
        var taskIdx = $(this).data("task-idx");
        var elementIdx = $('.task-element-button.element-button-active').data("element-idx");

        if ($(this).hasClass('param-name-active')) {
            var data = {
                "workflowID": workflowID,
                "taskIdx": taskIdx,
                "elementIdx": 0,
                "inputName": null,
                "outputName": null,
                "fileName": null,
            };
            var newURL = "/workflow/" + workflowID + "/task/" + taskIdx + "/element/" + elementIdx + "/";
            $('.task-param-name[data-param-name="' + paramName + '"]').removeClass('param-name-active');
        } else {
            var data = {
                "workflowID": workflowID,
                "taskIdx": taskIdx,
                "elementIdx": 0,
                "inputName": $(this).data('param-type') == 'input' ? $(this).data('param-name') : null,
                "outputName": $(this).data('param-type') == 'output' ? $(this).data('param-name') : null,
                "fileName": $(this).data('param-type') == 'file' ? $(this).data('param-name') : null,
            };
            var newURL = "/workflow/" + workflowID + "/task/" + taskIdx + "/element/" + elementIdx + "/" + paramType + "/" + paramName + "/";
            $('.task-param-name').removeClass('param-name-active');
            $('.task-param-name[data-param-name="' + paramName + '"]').addClass('param-name-active');
        }
        changeParameter(data);
        history.pushState(data, "", newURL);
    });

    // Handle clicking to change element:
    $('.task-row').on('click', '.task-element-button', function (evt) {
        var workflowID = $(this).data('wid');
        var taskIdx = $(this).data('task-idx');
        var elementIdx = $(this).data('element-idx');

        var param_name = $('.param-wrapper.param-active').data("param-name");
        var param_type = $('.param-wrapper.param-active').data("param-type");
        var inputName = null;
        var outputName = null;
        var fileName = null;
        if (param_type == 'input') {
            inputName = param_name
        } else if (param_type == 'output') {
            outputName = param_name
        } else if (param_type == 'file') {
            fileName = param_name
        }

        var data = {
            "workflowID": workflowID,
            "taskIdx": taskIdx,
            "elementIdx": elementIdx,
            "inputName": inputName,
            "outputName": outputName,
            "fileName": fileName,
        };
        var newURL = "/workflow/" + workflowID + "/task/" + taskIdx + "/element/" + elementIdx;
        if (param_type) {
            var newURL = newURL + "/" + param_type + "/" + param_name;
        }
        changeElement(data);
        history.pushState(data, "", newURL);
    });


    function updateTask(state) {
        // Compare state.taskIdx, state.elementIdx and state.input/output/fileName, to
        // see what we need to change:
        var currentTaskIdx = $('.task-wrapper.task-active').data("task-idx");
        var currentElementIdx = $('.task-element-button.element-button-active').data("element-idx");

        var param_name = $('.param-wrapper.param-active').data("param-name");
        var param_type = $('.param-wrapper.param-active').data("param-type");
        var currentInputName = null;
        var currentOutputName = null;
        var currentFileName = null;
        if (param_type == 'input') {
            currentInputName = param_name;
        } else if (param_type == 'output') {
            currentOutputName = param_name;
        } else if (param_type == 'file') {
            currentFileName = param_name;
        }

        if (currentTaskIdx != state.taskIdx) {
            console.log("need to change task; sending state: " + state);
            changeTask(state);
        } else if (currentElementIdx != state.elementIdx) {
            console.log("Need to change element; sending state: " + state);
            changeElement(state);
        } else {
            if (currentInputName != state.inputName) {
                console.log("need to change input; sending state: " + state);
            } else if (currentOutputName != state.outputName) {
                console.log("need to change output; sending state: " + state);
            } else if (currentFileName != state.fileName) {
                console.log("need to change file; sending state: " + state);
            }
            changeParameter(state);
        }

    }

    function changeElement(state) {

        var elementIdx = state.elementIdx;
        $('.task-element-button.element-button-active').removeClass('element-button-active');
        $('.task-element-button[data-element-idx=' + elementIdx + ']').addClass('element-button-active');

        $('.task-param-inspector.element-param-active').removeClass('element-param-active');
        $('.task-param-inspector[data-element-idx=' + elementIdx + ']').addClass('element-param-active');

        $('.task-duration.task-duration-active').removeClass('task-duration-active');
        $('.task-duration[data-element-idx="' + elementIdx + '"').addClass('task-duration-active');

        $('.task-resource-use.task-resource-use-active').removeClass('task-resource-use-active');
        $('.task-resource-use[data-element-idx="' + elementIdx + '"').addClass('task-resource-use-active');
    }

    function changeParameter(state) {
        $('.param-wrapper.param-active').removeClass('param-active');
        var paramName = state.inputName || state.outputName || state.fileName
        if (paramName) {
            $('.param-wrapper[data-param-name="' + paramName + '"]').addClass('param-active');
        }


    }

    function changeTask(state) {

        var workflowID = state.workflowID;
        var taskIdx = state.taskIdx;
        var elementIdx = state.elementIdx;

        $('#task-inspector-overlay').addClass('loading');
        $.ajax({
            type: 'POST',
            url: '/get_full_task',
            data: {
                "workflowID": workflowID,
                "taskIdx": taskIdx,
                "elementIdx": elementIdx,
            },
            success: function (response) {
                console.log("success!")
                $('.task-inspector').html(response);
                $('.task-wrapper.task-active').removeClass('task-active');
                $('.task-wrapper[data-task-idx=' + taskIdx + ']').addClass('task-active');
            },
            error: function (error) {
                console.log(error);
            },
            complete: function (data) {
                $('#task-inspector-overlay').removeClass('loading');
            }
        })
        if ($('#task-list-wrapper').hasClass('my-modal')) {
            $('#task-list-wrapper').removeClass('my-modal');
        };
    }


    function changeFigure(state) {

        var workflowID = state.workflowID;
        var figIdx = state.figIdx;

        console.log("requesting new figure idx: ", figIdx);

        $('#fig-inspector-overlay').addClass('loading');
        $.ajax({
            type: 'POST',
            url: '/get_full_figure',
            data: {
                "workflowID": workflowID,
                "figIdx": figIdx,
            },
            success: function (response) {
                console.log("success!")
                $('.fig-inspector').html(response);
                $('.fig-wrapper.task-active').removeClass('task-active');
                $('.fig-wrapper[data-fig-idx=' + figIdx + ']').addClass('task-active');
            },
            error: function (error) {
                console.log(error);
            },
            complete: function (data) {
                $('#fig-inspector-overlay').removeClass('loading');
            }
        })
        if ($('#task-list-wrapper').hasClass('my-modal')) {
            $('#task-list-wrapper').removeClass('my-modal');
        };
    };

    function findWorkflows(basePath) {
        $.ajax({
            type: 'POST',
            url: '/find_local_workflows',
            data: JSON.stringify({ "basePath": basePath }, null, '\t'),
            contentType: 'application/json;charset=UTF-8',
            success: function (response) {
                console.log("success!");
                $('#workflow-paths-table').html(response);
            },
            error: function (error) {
                console.log(error);
            },
            complete: function (data) {
                console.log("complete!");
                console.log(data);
            }
        })
    };

    var pathsTable = document.getElementById("workflow-paths-table");
    if (typeof (pathsTable) != 'undefined' && pathsTable != null) {
        console.log("div exists!");
        var basePath = pathsTable.getAttribute('data-search-path');
        basePath = basePath.replace(/<br>/gm, "");
        findWorkflows(basePath);
    }
    $('#search-dir-refresh-button').on("click", function (event) {
        var basePath = document.getElementById('search-dir-edit-button').innerHTML;
        basePath = basePath.replace(/<br>/gm, "");
        console.log(basePath);
        $('#workflow-paths-table').html('<div class="loader">Loading...</div>');
        findWorkflows(basePath);
    });


    $(window).on("popstate", function (event) {
        originalState = event.originalEvent.state;
        updateTask(originalState);
    });

    // Store initial state so it can be re-visited:
    var param_name = $('.param-wrapper.param-active').data("param-name");
    var param_type = $('.param-wrapper.param-active').data("param-type");
    var inputName = null;
    var outputName = null;
    var fileName = null;
    if (param_type == 'input') {
        inputName = param_name
    } else if (param_type == 'output') {
        outputName = param_name
    } else if (param_type == 'file') {
        fileName = param_name
    }
    history.replaceState({
        "workflowID": $('#wk-main').data('workflow-id'),
        "taskIdx": $('.task-wrapper.task-active').data("task-idx"),
        "elementIdx": $('.task-element-button.element-button-active').data("element-idx"),
        "inputName": inputName,
        "outputName": outputName,
        "fileName": fileName,
    }, document.title, document.location.href);

    async function getTaskParameters(workflowID, taskIdx) {

        const url = '/get_task_parameter_data/' + workflowID + '/' + taskIdx;
        const request = new Request(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const cacheName = 'task-parameter-data';
        let cachedData = await getCachedData(cacheName, request);

        if (cachedData) {
            console.log('Retrieved cached data');
            return cachedData;
        }

        console.log('Fetching fresh data');

        const cacheStorage = await caches.open(cacheName);
        await cacheStorage.add(request);
        cachedData = await getCachedData(cacheName, request);

        return cachedData;

    }

    // Get data from the cache.
    async function getCachedData(cacheName, request) {
        const cacheStorage = await caches.open(cacheName);
        const cachedResponse = await cacheStorage.match(request);

        if (!cachedResponse || !cachedResponse.ok) {
            return false;
        }

        return await cachedResponse.json();
    }


    function toFixed(value, precision) {
        var power = Math.pow(10, precision || 0);
        return String(Math.round(value * power) / power);
    }

    function arr2TableRow(arr) {
        console.log("arr2TableRow: arr: ", arr);
        var tableRow = "<tr>"
        for (var i = 0; i < arr.shape[0]; ++i) {
            var numStr = arr.get(i);
            if (arr.dtype.includes("float")) {
                numStr = toFixed(numStr, 4);
            }
            tableRow = tableRow + "<td>" + numStr + "</td>";
        }
        tableRow = tableRow + "</tr>"
        return tableRow
    }

    function ndarray2Table(arr) {
        var tableHTML = "<table class=\"ndarray\">";
        if (arr.ndims === 1) {
            var tableRow = "<tr>"
            for (var i = 0; i < arr.shape[0]; ++i) {
                var numStr = arr.get(i);
                if (arr.dtype.includes("float")) {
                    numStr = toFixed(numStr, 4);
                }
                tableRow = tableRow + "<td>" + numStr + "</td>";
            }
            tableRow = tableRow + "</tr>";
            tableHTML = tableHTML + tableRow;

        } else if (arr.ndims === 2) {
            console.log("2D array! shape: " + arr.shape);
            for (var i = 0; i < arr.shape[0]; i++) {
                var tableRow = "<tr>";
                for (var j = 0; j < arr.shape[1]; j++) {
                    var numStr = arr.get(i, j);
                    if (arr.dtype.includes("float")) {
                        numStr = toFixed(numStr, 4);
                    }
                    tableRow = tableRow + "<td>" + numStr + "</td>";
                }
                tableRow = tableRow + "</tr>";
                tableHTML = tableHTML + tableRow;
            };
        }
        tableHTML = tableHTML + "</table>";
        return tableHTML
    }

    function generateNestedParameterTable(obj) {
        // asymmetry exists here, this should work for just a value passed as obj.
        var ndarray = stdlib.ndarray.array;

        var tableHTML = "<table class=\"param-table\">";
        for (prop in obj) {
            tableHTML = tableHTML + "<tr>";
            tableHTML = tableHTML + "<td class=\"param-prop-name-cell\">" + prop + "</td>";
            if (Array.isArray(obj[prop])) {
                try {
                    var testArr = ndarray(obj[prop]);
                    var arrStr = ndarray2Table(testArr);
                } catch (error) {
                    var arrStr = obj[prop];
                };
                tableHTML = tableHTML + "<td>" + arrStr;
            } else if (typeof (obj[prop]) == "object") {
                tableHTML = tableHTML + "<td>" + generateNestedParameterTable(obj[prop]);
            } else {
                tableHTML = tableHTML + "<td class=\"param-prop-val-cell\">" + obj[prop];
            }
            tableHTML = tableHTML + "</td></tr>";
        }
        tableHTML = tableHTML + "</table>";
        return tableHTML;

    };

    function writeTaskParameterInspector(taskParameterData) {
        var paramInspector = '';
        for (const [inputName, elemVals] of Object.entries(taskParameterData['inputs'])) {
            paramInspector += '<div class="param-wrapper" data-param-type="input" data-param-name="' + inputName + '">';
            paramInspector += '<h4>Input: ' + inputName.replace('_', ' ') + '</h4>';
            for (let elemIdx = 0; elemIdx < elemVals.length; elemIdx++) {
                paramInspector += '<div class="task-param-inspector" data-element-idx="' + elemIdx + '">';
                paramInspector += generateNestedParameterTable(elemVals[elemIdx]);
                paramInspector += '</div>';
            };
            paramInspector += '</div>';
        };
        for (const [outputName, elemVals] of Object.entries(taskParameterData['outputs'])) {
            paramInspector += '<div class="param-wrapper" data-param-type="output" data-param-name="' + outputName + '">';
            paramInspector += '<h4>Output: ' + outputName.replace('_', ' ') + '</h4>';
            for (let elemIdx = 0; elemIdx < elemVals.length; elemIdx++) {
                paramInspector += '<div class="task-param-inspector" data-element-idx="' + elemIdx + '">';
                paramInspector += generateNestedParameterTable(elemVals[elemIdx]);
                paramInspector += '</div>';
            };
            paramInspector += '</div>';
        };
        return paramInspector;
    };

    document.getElementById("test-data-cache").addEventListener("click", function () {
        var workflowID = this.getAttribute('data-wid');
        var taskIdx = 0;
        console.log(workflowID, taskIdx);
        getTaskParameters(workflowID, taskIdx).then(data => {
            console.log(data);
            // const tableHTML = generateNestedParameterTable(data['outputs']['microstructure_seeds'][0]);
            // console.log(tableHTML);
            console.log(writeTaskParameterInspector(data));
        });
    });



});
